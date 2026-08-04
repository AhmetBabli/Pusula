"""
Kariyer Ajanı — Encryption Utilities (Fernet)
"""
import logging
from cryptography.fernet import Fernet, InvalidToken
from backend.config import settings

logger = logging.getLogger(__name__)

# Şifreleme objesini başlat
_fernet = Fernet(settings.ENCRYPTION_KEY)

def encrypt(value: str) -> str:
    """Metni şifreler ve base64 formatında döndürür."""
    if not value:
        return ""
    try:
        return _fernet.encrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"[Şifreleme Hatası] Veri şifrelenirken beklenmeyen bir sorun oluştu: {e}")
        return ""

def decrypt(token: str) -> str:
    """Base64 formatındaki şifreli metni çözer ve normal metni döndürür."""
    if not token:
        return ""
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        # Eski anahtarla şifrelenmiş veya bozulmuş bir veri gelirse sistemi çökertmek yerine boş döner
        logger.error("[Şifre Çözme Hatası] Geçersiz veya bozuk token tespit edildi! Şifreleme anahtarı (ENCRYPTION_KEY) değişmiş olabilir.")
        return ""
    except Exception as e:
        logger.error(f"[Şifre Çözme Hatası] Beklenmeyen hata: {e}")
        return ""