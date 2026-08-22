from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    # NULL: herkese açık, taranmış bir ilan (paylaşılan katalog).
    # Dolu: bir kullanıcının gelen kutusundan dönüştürdüğü ÖZEL bir fırsat —
    # o kullanıcının e-posta içeriğini taşıyabilir, bu yüzden sadece
    # sahibine gösterilmeli (bkz. routers/jobs.py list_jobs/get_job).
    owner_user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=True, index=True)

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

    notes = Column(Text, nullable=True)                # Kullanıcı notları

    # 🚀 Zaman fonksiyonları güncellendi
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # NOT: match_score/match_explanation/best_cv_id/missing_skills/status/
    # is_favorite artık burada DEĞİL — Job tüm kullanıcılar arasında paylaşılan
    # ortak bir katalog satırı, bu alanlar kullanıcıya özel olduğu için
    # JobUserState'e taşındı (bkz. backend/models/job_user_state.py).