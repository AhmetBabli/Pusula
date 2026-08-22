"""
Uygulamanın KENDİ adına gönderdiği sistem e-postaları (ör. şifre sıfırlama).

backend/automation/outreach_agent.py'den kasıtlı olarak ayrı: o, ÖĞRENCİNİN
kendi bağladığı Gmail hesabıyla (EmailAccount) bir ŞİRKETE gönderim yapıyor.
Bu modül ise uygulamanın kendi (SYSTEM_EMAIL_*) hesabıyla KULLANICIYA
gönderim yapıyor — farklı kimlik, farklı amaç.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.config import settings
from backend.exceptions import ExternalServiceError

logger = logging.getLogger("Mailer")


def send_system_email(to_email: str, subject: str, html_body: str) -> None:
    """Uygulamanın sistem hesabından e-posta gönderir.

    Yapılandırılmamışsa veya SMTP gönderimi başarısız olursa sessizce
    yutmak yerine ExternalServiceError fırlatır — aksi halde çağıran uç
    kullanıcıya "e-posta gönderildi" mesajı gösterip aslında hiçbir e-posta
    gitmemiş olurdu (bu oturumda defalarca düzeltilen sessiz-sahte-başarı
    hata sınıfının aynısı)."""
    if not settings.SYSTEM_EMAIL_ADDRESS or not settings.SYSTEM_EMAIL_APP_PASSWORD:
        raise ExternalServiceError(
            "Sistem e-posta gönderimi henüz yapılandırılmamış "
            "(SYSTEM_EMAIL_ADDRESS / SYSTEM_EMAIL_APP_PASSWORD eksik)."
        )

    msg = MIMEMultipart()
    msg["From"] = settings.SYSTEM_EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(settings.SYSTEM_EMAIL_ADDRESS, settings.SYSTEM_EMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Sistem e-postası gönderildi -> {to_email}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Sistem e-postası SMTP kimlik doğrulama hatası: {e}")
        raise ExternalServiceError("Sistem e-posta hesabının kimlik doğrulaması başarısız oldu.")
    except smtplib.SMTPException as e:
        logger.error(f"Sistem e-postası SMTP hatası: {e}")
        raise ExternalServiceError(f"E-posta gönderilemedi: {e}")
