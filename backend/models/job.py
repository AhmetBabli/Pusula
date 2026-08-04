from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from backend.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Kaynak bilgisi
    source = Column(String(50), nullable=False)        # kariyer_net, linkedin, youthall
    
    # 🚀 Güvenlik: Aynı ilanın tekrar eklenmesini önlemek için unique=True eklendi.
    # URL uzunluk limiti, uzun takip parametreleri yüzünden patlamasın diye 1000'e çıkarıldı.
    source_url = Column(String(1000), nullable=False, unique=True)   
    source_id = Column(String(200), nullable=True)     # Platformdaki benzersiz ID

    # İlan bilgileri
    title = Column(String(300), nullable=False)
    company = Column(String(200), nullable=False)
    company_logo_url = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)
    job_type = Column(String(50), default="staj")      # staj, tam_zamanlı, yarı_zamanlı
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    sector = Column(String(100), nullable=True)        # IT, Finans, Danışmanlık...

    # Tarihler
    posted_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    
    # 🚀 Zaman fonksiyonları güncellendi
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # AI Analizi
    match_score = Column(Float, default=0.0)           # 0-100
    match_explanation = Column(Text, nullable=True)    # Neden bu skor?
    best_cv_id = Column(Integer, nullable=True)        # En uygun CV
    
    # 🚀 Modern Yöntem: Text yerine SQLAlchemy native JSON tipi kullanıldı.
    missing_skills = Column(JSON, default=list)        # Eksik beceriler (Python listesi olarak döner)

    # Durum
    status = Column(String(30), default="new")
    # new → reviewed → applying → applied → interview → offer → rejected

    is_favorite = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)                # Kullanıcı notları

    # 🚀 Zaman fonksiyonları güncellendi
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))