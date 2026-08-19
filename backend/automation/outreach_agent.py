import re
import json
import base64
import requests
import smtplib
import logging
import os
from typing import Optional
from urllib.parse import urlparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google import genai
from google.genai import types
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
    async def find_job_contact_email(cls, job, api_key: Optional[str] = None) -> tuple[str, str, str]:
        """
        Bir ilan için başvuru e-postası bulur. Öncelik sırası:
        1. İlanın kendi metninde (description/requirements) geçen bir e-posta
           (birinci elden veri — en güvenilir kaynak).
        2. Bulunamazsa şirketin RESMİ web sitesi üzerinden arama (hunt_email) —
           tahmine dayalı, daha düşük güven ama iş ilanı sitelerinden değil
           doğrudan şirketin kendi kariyer/iletişim sayfasından geldiği için
           eski DuckDuckGo-metin-tarama yöntemine göre çok daha isabetli.
        Döndürür: (email_veya_bos_string, kaynak, kaynak_url) — kaynak:
        "job_posting" | "company_site" | "". kaynak_url, kullanıcının onaydan
        önce tıklayıp gerçekten şirketin sitesi mi diye kontrol edebileceği bir
        şeffaflık linki (job_posting'de zaten ilanın kendisi olduğu için boş).
        """
        text = " ".join(filter(None, [getattr(job, "description", None), getattr(job, "requirements", None)]))
        if text:
            invalid_extensions = ("png", "jpg", "jpeg", "gif", "w3.org", "sentry.io")
            found = [e.lower() for e in cls.EMAIL_REGEX.findall(text) if not e.lower().endswith(invalid_extensions)]
            if found:
                logger.info(f"[{job.company}] İlan metninden e-posta bulundu: {found[0]}")
                return found[0], "job_posting", ""

        email, source_url = await cls.hunt_email_with_source(job.company, api_key=api_key)
        if email:
            return email, "company_site", source_url

        return "", "", ""

    @staticmethod
    def _domain_core(url_or_domain: str) -> str:
        """Bir URL veya alan adından, karşılaştırmaya uygun 'çekirdek' ismi
        çıkarır: 'mail.sirket.com.tr' -> 'sirket'. Mükemmel değil (ör. .co.uk
        gibi bileşik TLD'lerde yanılabilir) ama e-posta/site alan adı
        eşleşmesini kabaca doğrulamak için yeterince pratik."""
        domain = urlparse(url_or_domain).netloc or url_or_domain
        domain = domain.lower().removeprefix("www.")
        known_suffixes = {"com", "co", "org", "net", "gov", "edu", "tr", "io", "biz", "info"}
        parts = [p for p in domain.split(".") if p and p not in known_suffixes]
        return parts[-1] if parts else domain

    @classmethod
    async def hunt_email(cls, company_name: str, api_key: Optional[str] = None) -> str:
        """Geriye dönük uyumluluk için: sadece e-postayı döner. Kaynak URL'i
        de gerekiyorsa (ör. kullanıcıya şeffaflık için göstermek) hunt_email_with_source
        kullanın — ikisi de aynı Gemini çağrısını paylaşır."""
        email, _source_url = await cls.hunt_email_with_source(company_name, api_key=api_key)
        return email

    @classmethod
    async def hunt_email_with_source(cls, company_name: str, api_key: Optional[str] = None) -> tuple[str, str]:
        """
        Şirketin resmi web sitesini bulur (Gemini + Google Search grounding),
        kariyer/İK/iletişim sayfalarına bakar ve orada geçen bir e-posta adresi
        döndürür. Üçüncü parti iş ilanı sitelerinden değil, doğrudan şirketin
        kendi alan adından bilgi kullanılır (daha yüksek güven).

        Ek doğrulama: bulunan e-postanın alan adı, Gemini'nin "resmi site"
        olarak işaretlediği URL'in alan adıyla örtüşmüyorsa reddedilir —
        model bazen alakasız bir e-posta ile alakasız bir "kaynak" sitesini
        aynı yanıtta birleştirebiliyor, bu basit çapraz kontrol o durumu yakalar.

        Döndürür: (email_veya_bos_string, source_url_veya_bos_string)
        """
        effective_key = api_key or settings.GEMINI_API_KEY
        if not effective_key:
            return "", ""

        prompt = f"""Google araması kullanarak "{company_name}" şirketinin RESMİ web sitesini bul.
O sitenin kariyer, insan kaynakları veya iletişim sayfasına bak ve başvuru/İK
iletişimi için kullanılabilecek bir e-posta adresi ara.

Kurallar:
- SADECE şirketin kendi resmi alan adından bilgi kullan (LinkedIn, Kariyer.net,
  Youthall gibi üçüncü parti iş ilanı sitelerinden veya sosyal medyadan DEĞİL).
- Gerçek bir e-posta bulamazsan veya emin değilsen "email" alanını boş bırak,
  ASLA uydurma/tahmini bir e-posta üretme.

Yanıtı SADECE şu JSON formatında ver, başka açıklama ekleme:
{{"email": "...", "source_url": "..."}}"""

        try:
            client = genai.Client(api_key=effective_key)
            config = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL, contents=prompt, config=config
            )
            text = (response.text or "").strip()

            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                logger.info(f"[{company_name}] Gemini yanıtında JSON bulunamadı.")
                return "", ""

            data = json.loads(match.group())
            email = (data.get("email") or "").strip().lower()
            source_url = (data.get("source_url") or "").strip()
            invalid_extensions = ("png", "jpg", "jpeg", "gif", "w3.org", "sentry.io", "example.com", "google.com")
            if not (email and cls.EMAIL_REGEX.fullmatch(email) and not email.endswith(invalid_extensions)):
                logger.info(f"[{company_name}] Şirket sitesinde geçerli bir e-posta bulunamadı.")
                return "", ""

            if source_url:
                email_core = cls._domain_core(email.split("@")[-1])
                site_core = cls._domain_core(source_url)
                if email_core != site_core:
                    logger.warning(
                        f"[{company_name}] Alan adı uyuşmazlığı — e-posta '{email}' (çekirdek: {email_core}) "
                        f"ile kaynak site '{source_url}' (çekirdek: {site_core}) örtüşmüyor, reddedildi."
                    )
                    return "", ""

            logger.info(f"[{company_name}] Şirket sitesinden e-posta bulundu: {email} (kaynak: {source_url})")
            return email, source_url
        except Exception as e:
            logger.error(f"[{company_name}] Beklenmeyen hata (hunt_email_with_source): {e}")
            return "", ""

    @staticmethod
    def _safe_attachment_filename(cv_path: str, preferred_name: Optional[str] = None) -> str:
        """Eke gidecek dosya adını belirler: mümkünse CV'nin (kullanıcıya anlamlı)
        başlığını kullanır, diskteki rastgele/zaman damgalı depolama adını değil.
        Dosya sisteminde/e-posta istemcilerinde sorun çıkarabilecek karakterleri temizler."""
        ext = os.path.splitext(cv_path)[1] or ".pdf"
        name = (preferred_name or "").strip()
        if not name:
            return os.path.basename(cv_path)

        name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
        if not name:
            return os.path.basename(cv_path)
        if not os.path.splitext(name)[1]:
            name += ext
        return name

    @staticmethod
    def _build_mime_message(
        sender_email: str,
        target_email: str,
        subject: str,
        html_body: str,
        cv_path: Optional[str] = None,
        cv_filename: Optional[str] = None,
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
                    attachment_name = OutreachAgent._safe_attachment_filename(cv_path, cv_filename)
                    with open(cv_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=attachment_name)
                    part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
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
        smtp_port: int = 587,
        cv_filename: Optional[str] = None,
    ) -> bool:
        """
        SMTP + uygulama şifresi kullanarak hedef maile içeriği ve varsa CV'yi gönderir.
        """
        if not target_email:
            logger.error("Hedef e-posta adresi boş olamaz.")
            return False

        msg = cls._build_mime_message(sender_email, target_email, subject, html_body, cv_path, cv_filename)
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
        cv_filename: Optional[str] = None,
    ) -> bool:
        """Google OAuth (gmail.send izni) ile, uygulama şifresi olmadan doğrudan Gmail API üzerinden gönderir."""
        if not target_email:
            logger.error("Hedef e-posta adresi boş olamaz.")
            return False

        msg = cls._build_mime_message(sender_email, target_email, subject, html_body, cv_path, cv_filename)
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
        cv_filename: Optional[str] = None,
    ) -> bool:
        """EmailAccount'un bağlantı yöntemine göre (OAuth veya uygulama şifresi) gönderim yapar."""
        if getattr(account, "auth_method", "app_password") == "oauth":
            access_token = cls.refresh_google_access_token(account.oauth_refresh_token)
            if not access_token:
                logger.error("Google erişim token'ı alınamadı, gönderim iptal edildi.")
                return False
            return cls.send_via_gmail_api(access_token, account.email, target_email, subject, html_body, cv_path, cv_filename)

        return cls.send_cold_email(
            sender_email=account.email,
            app_password=account.app_password,
            target_email=target_email,
            subject=subject,
            html_body=html_body,
            cv_path=cv_path,
            cv_filename=cv_filename,
        )