from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from backend.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # Kaynak
    source = Column(String(50), nullable=False)        # youthall, kommunity, meetup, eventbrite
    
    # 🚀 Güvenlik: Aynı etkinliğin defalarca eklenmesini önlemek için unique=True eklendi.
    # URL uzunluk limiti uzun takip parametreleri yüzünden patlamasın diye 1000'e çıkarıldı.
    source_url = Column(String(1000), nullable=False, unique=True)
    source_id = Column(String(200), nullable=True)

    # Etkinlik bilgileri
    title = Column(String(300), nullable=False)
    organizer = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=False)    # hackathon, career_fair, seminar, networking, workshop
    location = Column(String(200), nullable=True)      # "Online" veya fiziksel adres
    is_online = Column(Boolean, default=False)
    is_free = Column(Boolean, default=True)

    # Tarihler
    event_date = Column(DateTime, nullable=True)
    registration_deadline = Column(DateTime, nullable=True)
    
    # 🚀 Zaman fonksiyonları güncellendi (lambda kullanıldı)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # AI Analizi
    relevance_score = Column(Float, default=0.0)       # 0-100
    relevance_reason = Column(Text, nullable=True)

    # Not: status BURADA yok — Event tüm kullanıcılar arasında paylaşılan bir
    # katalog, durum ise kullanıcıya özel (bkz. EventUserState). JobUserState'in
    # Job için çözdüğü sınıf hatanın aynısı: herhangi bir kullanıcının PATCH'i
    # herkesin durumunu ezmesin diye.
    notes = Column(Text, nullable=True)

    # 🚀 Zaman fonksiyonları güncellendi
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))