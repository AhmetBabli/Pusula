"""
Kariyer Ajanı — Application Configuration
"""
import os
import secrets
import warnings
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    """Centralized application settings."""

    # Project
    APP_NAME: str = "Kariyer Ajanı"
    APP_VERSION: str = "1.0.0"
    # "fail closed": DEBUG env değişkeni unutulursa (ör. bir production deploy'da)
    # uygulama üretim moduna düşsün, yanlışlıkla debug modunda açılıp CORS'u
    # wildcard'a, /docs'u herkese açık bırakmasın.
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite, postgresql
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).parent.parent / 'kariyer_ajani.db'}"
    )
    
    # Validate DATABASE_TYPE
    if DATABASE_TYPE not in ["sqlite", "postgresql"]:
        raise ValueError(f"DATABASE_TYPE must be 'sqlite' or 'postgresql', got '{DATABASE_TYPE}'")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))

    # AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # "gemini-2.0-flash" Google tarafından kaldırıldı (404). "-latest" bir alias
    # olduğu için Google modeli rotasyona soktukça burayı elle güncellemeye gerek
    # kalmıyor — aynı sessiz kırılma bir daha yaşanmasın diye.
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

    # Mülakat Koçu'nun sesli soru okuması için Google Cloud Text-to-Speech.
    # Kullanıcı bazlı değil, uygulama genelinde tek bir anahtar — her öğrenciden
    # kendi Google Cloud faturalandırmasını kurmasını istemek makul değil.
    GOOGLE_TTS_API_KEY: str = os.getenv("GOOGLE_TTS_API_KEY", "")

    # Scraping
    SCRAPE_INTERVAL_HOURS: int = 6
    MAX_PAGES_PER_SCRAPE: int = 5

    # Inbox — her yeni e-posta bir Gemini sınıflandırma çağrısı tüketir, o yüzden
    # iş taramasından daha temkinli bir aralıkta çalışıyor (paylaşılan ücretsiz
    # kotayı arka planda sessizce tüketmesin diye).
    INBOX_SYNC_INTERVAL_MINUTES: int = 120

    # File upload limits
    MAX_UPLOAD_SIZE_MB: int = 5

    # Email / Gmail
    IMAP_SERVER: str = "imap.gmail.com"
    IMAP_PORT: int = 993

    # Google OAuth (Sign in with Google + Gmail gönderim izni)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    CV_STORE_PATH: Path = PROJECT_ROOT / "cv_store"
    LOGS_PATH: Path = PROJECT_ROOT / "logs"

    # CORS — dynamically narrow down for production
    _dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
    ]
    _prod_origins = [
        "https://senin-domainin.com", # İleride buraya frontend'in canlı URL'sini yazacaksın
    ]
    ALLOWED_ORIGINS: list = _dev_origins if DEBUG else _prod_origins

    def __init__(self):
        # 📁 1. Klasörleri otomatik oluştur (Yoksa çökmeyi engeller)
        self.CV_STORE_PATH.mkdir(parents=True, exist_ok=True)
        self.LOGS_PATH.mkdir(parents=True, exist_ok=True)

        # 🔐 2. Encryption Key Yönetimi (Zombi verileri engelle)
        _enc_key_raw = os.getenv("ENCRYPTION_KEY", "")
        if _enc_key_raw:
            self.ENCRYPTION_KEY = _enc_key_raw.encode()
        else:
            if not self.DEBUG:
                raise ValueError(
                    "⛔ Üretimde ENCRYPTION_KEY zorunludur! "
                    ".env dosyasında geçerli bir Fernet anahtarı ayarlayın. "
                    "Generate: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )
            # ⚠️ DEV MODE WARNING: Dynamically generate, never commit to repo
            from cryptography.fernet import Fernet
            self.ENCRYPTION_KEY = Fernet.generate_key()
            warnings.warn(
                "⚠️ ENCRYPTION_KEY .env'de bulunamadı. Geliştirme için TEMPORARY anahtar oluşturuldu.",
                stacklevel=2,
            )

        # 🔒 3. Güvenlik uyarıları
        weak_keys = ["dev-secret-key-change-in-production", "change-this-in-production", ""]
        if self.SECRET_KEY in weak_keys:
            if not self.DEBUG:
                raise ValueError(
                    "⛔ Üretimde zayıf SECRET_KEY kullanılamaz! "
                    ".env dosyasında güçlü bir anahtar ayarlayın."
                )
            warnings.warn(
                "⚠️ Zayıf SECRET_KEY tespit edildi. Üretimde güçlü bir anahtar kullanın.",
                stacklevel=2,
            )

        if not self.GEMINI_API_KEY and not self.DEBUG:
            raise ValueError(
                "⛔ Üretimde GEMINI_API_KEY zorunludur. .env dosyanıza anahtar ekleyin."
            )


settings = Settings()