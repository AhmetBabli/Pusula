import re
import base64
import requests
import smtplib
import logging
import os
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from bs4 import BeautifulSoup
from backend.config import settings

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("OutreachAgent")

class OutreachAgent:
    """
    Cold Outreach Agent: Şirketlerin iletişim/IK e-postalarını bulur
    ve güvenli SMTP bağlantısı üzerinden özgeçmiş ve kapak mektubunu iletir.
    """
    
    # Regex işlemini sınıf seviyesinde bir kez derleyerek performansı artırıyoruz
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    @classmethod
    def find_job_contact_email(cls, job) -> tuple[str, str]:
        """
        Bir ilan için başvuru e-postası bulur. Öncelik sırası:
        1. İlanın kendi metninde (description/requirements) geçen bir e-posta
           (birinci elden veri — en güvenilir kaynak).
        2. Bulunamazsa şirket adına göre web araması (hunt_email) — tahmine
           dayalı, daha düşük güven.
        Döndürür: (email_veya_bos_string, kaynak) — kaynak: "job_posting" | "web_search" | ""
        """
        text = " ".join(filter(None, [getattr(job, "description", None), getattr(job, "requirements", None)]))
        if text:
            invalid_extensions = ("png", "jpg", "jpeg", "gif", "w3.org", "sentry.io")
            found = [e.lower() for e in cls.EMAIL_REGEX.findall(text) if not e.lower().endswith(invalid_extensions)]
            if found:
                logger.info(f"[{job.company}] İlan metninden e-posta bulundu: {found[0]}")
                return found[0], "job_posting"

        guessed = cls.hunt_email(job.company)
        if guessed:
            return guessed, "web_search"

        return "", ""

    @classmethod
    def hunt_email(cls, company_name: str) -> str:
        """
        Arama motoru üzerinden firmanın insan kaynakları veya iletişim mailini arar.
        """
        query = f'"{company_name}" (ik OR "insan kaynakları" OR kariyer OR info OR iletisim OR contact) mail "@"'
        url = "https://html.duckduckgo.com/html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        try:
            res = requests.post(url, data={'q': query}, headers=headers, timeout=15)
            res.raise_for_status() # HTTP hatalarını (404, 500 vb.) yakalamak için
            
            soup = BeautifulSoup(res.text, "html.parser")
            text_content = soup.get_text()
            
            emails = cls.EMAIL_REGEX.findall(text_content)
            
            # Filtreleme: İstenmeyen uzantıları/domainleri çıkar
            # (duckduckgo.com dahil — arama motorunun kendi sayfa metninden sızan,
            # şirketle hiçbir ilgisi olmayan adresleri elemek için)
            invalid_extensions = ("png", "jpg", "jpeg", "gif", "w3.org", "sentry.io", "duckduckgo.com", "example.com")
            valid_emails = [e.lower() for e in set(emails) if not e.lower().endswith(invalid_extensions)]
            
            if not valid_emails:
                logger.info(f"[{company_name}] için geçerli bir e-posta adresi bulunamadı.")
                return ""
                
            # Öncelikli IK ve Kariyer maillerini kontrol et
            priority_keywords = ["ik@", "kariyer@", "hr@", "insankaynaklari@", "recruitment@"]
            for email in valid_emails:
                if any(keyword in email for keyword in priority_keywords):
                    logger.info(f"[{company_name}] Öncelikli hedef bulundu: {email}")
                    return email
                    
            # Fallback: Info ve İletişim
            for email in valid_emails:
                if "info@" in email or "iletisim@" in email:
                    logger.info(f"[{company_name}] İkincil hedef bulundu: {email}")
                    return email
            
            # Kriterlere uymayan ama geçerli ilk adresi döndür
            logger.info(f"[{company_name}] Genel e-posta bulundu: {valid_emails[0]}")
            return valid_emails[0]
            
        except requests.RequestException as e:
            logger.error(f"[{company_name}] Ağ veya istek hatası: {e}")
            return ""
        except Exception as e:
            logger.critical(f"[{company_name}] Beklenmeyen hata (hunt_email): {e}")
            return ""

    @staticmethod
    def _build_mime_message(
        sender_email: str,
        target_email: str,
        subject: str,
        html_body: str,
        cv_path: Optional[str] = None,
    ) -> Optional[MIMEMultipart]:
        """Ortak MIME mesaj inşası (SMTP ve Gmail API gönderim yolları bunu paylaşır)."""
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = subject

        # Karakter kodlaması UTF-8 olarak belirlenmeli (Türkçe karakter sorunu yaşamamak için)
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if cv_path:
            if os.path.exists(cv_path) and os.path.isfile(cv_path):
                try:
                    with open(cv_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(cv_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(cv_path)}"'
                    msg.attach(part)
                except IOError as e:
                    logger.error(f"CV dosyası okunamadı: {e}")
                    return None
            else:
                logger.warning(f"Belirtilen CV yolu geçersiz veya dosya bulunamadı: {cv_path}")
                return None

        return msg

    @classmethod
    def send_cold_email(
        cls,
        sender_email: str,
        app_password: str,
        target_email: str,
        subject: str,
        html_body: str,
        cv_path: Optional[str] = None,
        smtp_host: str = 'smtp.gmail.com',
        smtp_port: int = 587
    ) -> bool:
        """
        SMTP + uygulama şifresi kullanarak hedef maile içeriği ve varsa CV'yi gönderir.
        """
        if not target_email:
            logger.error("Hedef e-posta adresi boş olamaz.")
            return False

        msg = cls._build_mime_message(sender_email, target_email, subject, html_body, cv_path)
        if msg is None:
            return False

        # E-posta Gönderimi (Context Manager kullanımı ile güvenli kapatma)
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(sender_email, app_password)
                server.send_message(msg)

            logger.info(f"E-posta başarıyla gönderildi -> {target_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Kimlik Doğrulama Hatası: Uygulama şifresini veya gönderici mailini kontrol edin.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP İletişim Hatası: {e}")
            return False
        except Exception as e:
            logger.critical(f"Beklenmeyen hata (send_cold_email): {e}")
            return False

    @staticmethod
    def refresh_google_access_token(refresh_token: str) -> Optional[str]:
        """Google OAuth refresh token'ı ile kısa ömürlü bir access token üretir."""
        if not refresh_token or not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return None
        try:
            res = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=10,
            )
            if not res.ok:
                logger.error(f"Google access token yenilenemedi: {res.status_code} {res.text}")
                return None
            return res.json().get("access_token")
        except Exception as e:
            logger.error(f"Google token yenileme hatası: {e}")
            return None

    @classmethod
    def send_via_gmail_api(
        cls,
        access_token: str,
        sender_email: str,
        target_email: str,
        subject: str,
        html_body: str,
        cv_path: Optional[str] = None,
    ) -> bool:
        """Google OAuth (gmail.send izni) ile, uygulama şifresi olmadan doğrudan Gmail API üzerinden gönderir."""
        if not target_email:
            logger.error("Hedef e-posta adresi boş olamaz.")
            return False

        msg = cls._build_mime_message(sender_email, target_email, subject, html_body, cv_path)
        if msg is None:
            return False

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        try:
            res = requests.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={"raw": raw},
                timeout=20,
            )
            if res.ok:
                logger.info(f"[Gmail API] E-posta başarıyla gönderildi -> {target_email}")
                return True
            logger.error(f"[Gmail API] Gönderim başarısız: {res.status_code} {res.text}")
            return False
        except Exception as e:
            logger.critical(f"[Gmail API] Beklenmeyen hata: {e}")
            return False

    @classmethod
    def send_via_account(
        cls,
        account,
        target_email: str,
        subject: str,
        html_body: str,
        cv_path: Optional[str] = None,
    ) -> bool:
        """EmailAccount'un bağlantı yöntemine göre (OAuth veya uygulama şifresi) gönderim yapar."""
        if getattr(account, "auth_method", "app_password") == "oauth":
            access_token = cls.refresh_google_access_token(account.oauth_refresh_token)
            if not access_token:
                logger.error("Google erişim token'ı alınamadı, gönderim iptal edildi.")
                return False
            return cls.send_via_gmail_api(access_token, account.email, target_email, subject, html_body, cv_path)

        return cls.send_cold_email(
            sender_email=account.email,
            app_password=account.app_password,
            target_email=target_email,
            subject=subject,
            html_body=html_body,
            cv_path=cv_path,
        )