import imaplib
import email
from email.policy import default
from email.header import decode_header
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional
import bs4
import logging
from backend.config import settings

# Loglama yapılandırması
logger = logging.getLogger("GmailService")

class GmailService:
    """
    Gmail Intelligence Service: Handles IMAP connections and robust email parsing.
    """

    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password
        self.mail: Optional[imaplib.IMAP4_SSL] = None

    def __enter__(self):
        """Context manager desteği: 'with GmailService(...) as service:' kullanımı için."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """İşlem bitince veya hata alınca bağlantıyı güvenle kapatır."""
        self.disconnect()

    def connect(self) -> bool:
        """IMAP bağlantısını güvenli bir şekilde kurar."""
        try:
            self.mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
            self.mail.login(self.email_address, self.app_password)
            self.mail.select("inbox")
            logger.info("IMAP bağlantısı başarıyla kuruldu.")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP kimlik doğrulama veya sunucu hatası: {e}")
            self.mail = None
            return False
        except Exception as e:
            logger.critical(f"Beklenmeyen bağlantı hatası: {e}")
            self.mail = None
            return False

    def fetch_latest_emails(self, limit: int = 10) -> List[dict]:
        """Son e-postaları çeker ve ayrıştırılmış veri olarak döndürür."""
        if not self.mail:
            if not self.connect():
                return []

        # Locale-bağımsız IMAP tarih formatı (RFC 3501)
        # strftime locale'e göre değişebildiği için İngilizce ayları sabitliyoruz.
        eng_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        thirty_days_ago = date.today() - timedelta(days=30)
        safe_date_str = f"{thirty_days_ago.day}-{eng_months[thirty_days_ago.month - 1]}-{thirty_days_ago.year}"
        search_criterion = f'(SINCE "{safe_date_str}")'
        
        try:
            status, messages = self.mail.search(None, search_criterion)
            if status != 'OK' or not messages[0]:
                logger.info("Belirtilen kriterlerde e-posta bulunamadı.")
                return []

            mail_ids = messages[0].split()
            mail_ids.sort(key=int, reverse=True)
            latest_ids = mail_ids[:limit]

            results = []
            for m_id in latest_ids:
                status, data = self.mail.fetch(m_id, '(RFC822)')
                if status != 'OK' or not data:
                    continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email, policy=default)
                
                # Başlıkları güvenli bir şekilde decode et
                subject = self._decode_header(msg.get('Subject', '(No Subject)'))
                sender = self._decode_header(msg.get('From', '(Unknown Sender)'))
                
                # Tarih ayrıştırma
                date_str = msg.get('Date')
                try:
                    received_at = email.utils.parsedate_to_datetime(date_str)
                except (TypeError, ValueError):
                    received_at = datetime.now(timezone.utc) # utcnow() yerine modern kullanım

                # Gövde ayrıştırma ve temizleme
                body = self._extract_body(msg)
                clean_body = self._clean_content(body)

                results.append({
                    "uid": m_id.decode('ascii', errors='ignore'),
                    "subject": subject,
                    "sender": sender,
                    "body": clean_body,
                    "received_at": received_at
                })

            return results
            
        except Exception as e:
            logger.error(f"E-postaları çekerken hata oluştu: {e}")
            return []

    @staticmethod
    def _decode_header(header_value: str) -> str:
        """IMAP başlıklarındaki =?utf-8?Q? tarzı şifrelemeleri normal metne çevirir."""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(encoding or 'utf-8', errors='replace'))
                except LookupError:
                    # Geçersiz veya bilinmeyen encoding durumunda fallback
                    result.append(part.decode('utf-8', errors='replace'))
            else:
                result.append(str(part))
        return "".join(result)

    def _extract_body(self, msg) -> str:
        """MIME mesajından düz metin gövdesini güvenli bir şekilde çıkarır."""
        body_text = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    continue
                    
                if content_type in ["text/plain", "text/html"]:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                        
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        decoded_text = payload.decode(charset, errors='replace')
                    except LookupError:
                        decoded_text = payload.decode('utf-8', errors='replace')
                        
                    if content_type == "text/html":
                        decoded_text = self._html_to_text(decoded_text)
                    
                    # Eğer hem plain hem html varsa üzerine yazmamak için (veya birini tercih edebilirsin)
                    # Genellikle multipart/alternative yapısında en iyi format sona eklenir.
                    body_text = decoded_text
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    body_text = payload.decode(charset, errors='replace')
                except LookupError:
                    body_text = payload.decode('utf-8', errors='replace')
                
                if msg.get_content_type() == "text/html":
                    body_text = self._html_to_text(body_text)

        return body_text

    def _html_to_text(self, html: str) -> str:
        """HTML'i temiz bir düz metne dönüştürür."""
        if not html:
            return ""
        soup = bs4.BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style", "head", "title", "meta"]):
            script.extract()
        return soup.get_text(separator='\n').strip()

    def _clean_content(self, body: str) -> str:
        """E-posta imzalarını ve yanıt alıntılarını (quotes) temizler."""
        if not body:
            return ""
            
        lines = body.splitlines()
        clean_lines = []
        
        delimiters = [
            "---Original Message---",
            "From:",
            "________________________________",
            "On ", "wrote:"
        ]

        for line in lines:
            line_stripped = line.strip()
            
            # Alıntı başlangıç tespiti
            if any(delim in line_stripped for delim in delimiters) and (":" in line_stripped or "---" in line_stripped):
                break
                
            if line_stripped.startswith(">"):
                continue
                
            if line_stripped in ["--", "Get Outlook for iOS", "Sent from my iPhone"]:
                break
                
            clean_lines.append(line)

        return "\n".join(clean_lines).strip()

    def disconnect(self):
        """Bağlantıyı ve oturumu güvenli bir şekilde kapatır."""
        if self.mail:
            try:
                # Durumu kontrol et, kapalıysa hata vermesin
                if self.mail.state == 'SELECTED':
                    self.mail.close()
                if self.mail.state != 'LOGOUT':
                    self.mail.logout()
            except Exception as e:
                logger.debug(f"IMAP kapatılırken önemsiz hata: {e}")
            finally:
                self.mail = None
                logger.info("IMAP bağlantısı kapatıldı.")