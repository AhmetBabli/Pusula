from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from backend.database import Base

class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 🚀 Veritabanı Güvenliği: Kullanıcı silinirse, ona ait CV'ler de otomatik silinir (Cascade)
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=False)       # "AI Odaklı CV", "Siber Güvenlik CV"
    variant_type = Column(String(50), nullable=False)  # ai, cyber, it, general
    file_path = Column(String(500), nullable=True)     # PDF dosya yolu
    extracted_text = Column(Text, nullable=True)       # PDF'den çıkarılmış metin

    # AI Analizi
    ats_score = Column(Float, default=0.0)             # 0-100
    ats_feedback = Column(Text, nullable=True)         # AI geri bildirim
    
    # 🚀 Modern Yöntem: Text yerine SQLAlchemy native JSON tipi kullanıldı.
    # Varsayılan olarak boş liste (list) döner.
    target_keywords = Column(JSON, default=list)       # Hedef anahtar kelimeler
    strengths = Column(JSON, default=list)             # Güçlü yönler
    weaknesses = Column(JSON, default=list)            # Zayıf yönler

    is_default = Column(Boolean, default=False)
    is_ai_generated = Column(Boolean, default=False)   # AI tarafından oluşturuldu mu

    # 🚀 Zaman fonksiyonları güncellendi (Lambda kullanarak her kayıtta anlık tetiklenir)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))