from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.utils.crypto import encrypt, decrypt

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)

    # 🚀 Hesap sahibi: kullanıcı silinirse bağlı e-posta hesapları da silinir (Cascade)
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)

    email = Column(String(200), nullable=False, unique=True)
    _app_password = Column("app_password", String(500), nullable=False, default="")  # Encrypted
    provider = Column(String(50), default="gmail")
    is_active = Column(Boolean, default=True)

    # "app_password" (IMAP + uygulama şifresi) veya "oauth" (Google ile bağlanıp
    # gmail.send iznini verdiği için doğrudan Gmail API üzerinden gönderim)
    auth_method = Column(String(20), default="app_password", nullable=False)
    _oauth_refresh_token = Column("oauth_refresh_token", String(1000), nullable=True)  # Encrypted

    # 🚀 Zaman fonksiyonu güncellendi
    last_sync = Column(DateTime, nullable=True)

    items = relationship("InboxItem", back_populates="account", cascade="all, delete-orphan")

    @property
    def app_password(self) -> str:
        return decrypt(self._app_password)

    @app_password.setter
    def app_password(self, value: str):
        self._app_password = encrypt(value)

    @property
    def oauth_refresh_token(self) -> str:
        return decrypt(self._oauth_refresh_token) if self._oauth_refresh_token else ""

    @oauth_refresh_token.setter
    def oauth_refresh_token(self, value: str):
        self._oauth_refresh_token = encrypt(value) if value else None

class InboxItem(Base):
    __tablename__ = "inbox_items"

    id = Column(Integer, primary_key=True, index=True)
    
    # 🚀 DB seviyesinde Cascade eklendi
    account_id = Column(Integer, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False)
    
    # "job" or "event"
    item_type = Column(String(50), nullable=False)
    
    title = Column(String(500), nullable=False)
    sender = Column(String(200), nullable=False)
    body_summary = Column(Text, nullable=True)
    content_original = Column(Text, nullable=True)
    
    received_at = Column(DateTime, nullable=False)
    
    # 🚀 Zaman fonksiyonu güncellendi (lambda kullanarak her kayıtta yeni zaman üretmesi sağlandı)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    is_read = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)
    
    # 🚀 Tekil unique kaldırıldı, aşağıda tablo seviyesine taşındı
    uid = Column(String(100), nullable=False)

    account = relationship("EmailAccount", back_populates="items")

    # 🚀 ÇÖZÜM: Aynı posta kutusundaki UID benzersizdir. 
    # Account_id ve uid ikilisi birlikte benzersiz olmak zorundadır.
    __table_args__ = (
        UniqueConstraint('account_id', 'uid', name='_account_uid_uc'),
    )