from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from backend.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)

    # 🚀 Başvuru sahibi: kullanıcı silinirse başvuruları da silinir (Cascade)
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)

    # 🚀 Veritabanı Güvenliği: İlan veya CV silinirse, başvuru da otomatik silinir (Cascade)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    cv_id = Column(Integer, ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)

    # Durum
    status = Column(String(30), default="draft")
    # draft → awaiting_approval → approved → submitted → response_received → interview → offer → rejected

    # Başvuru verileri (JSON native formatı doğru kullanılmış)
    form_data = Column(JSON, nullable=True)            # Doldurulmuş form alanları

    # Başvuru formlarında sık sorulan sorulara kopyala-yapıştıra hazır,
    # CV+ilana özel AI cevapları: [{"question": "...", "answer": "..."}]
    qa_answers = Column(JSON, nullable=True)

    # 🚀 Mektup silinirse başvuru kalmaya devam etsin, sadece referansı kopsun (SET NULL)
    cover_letter_id = Column(Integer, ForeignKey("cover_letters.id", ondelete="SET NULL"), nullable=True)

    # E-posta ile onaylı gönderim: hedef adres, kaynağı ve gönderim durumu
    contact_email = Column(String(300), nullable=True)
    contact_email_source = Column(String(20), nullable=True)  # job_posting | web_search | manual
    send_status = Column(String(20), default="not_applicable")  # not_applicable | pending | sent | failed
    send_error = Column(Text, nullable=True)

    # Mezun/referans bulucu: [{"name","title","search_hint","message_draft"}]
    # — tekrar tekrar Gemini çağırmamak için sonuç burada cache'lenir.
    referral_candidates = Column(JSON, nullable=True)

    # Başvuru sonrası takip: gerçekten gönderilmiş bir takip e-postası varsa
    # ne zaman gönderildiği — nudge'ın tekrar tekrar önerilmesini engeller.
    followup_sent_at = Column(DateTime, nullable=True)

    # Kullanıcı notları
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)     # Kullanıcı neden reddetti

    # Tarihler
    submitted_at = Column(DateTime, nullable=True)
    response_at = Column(DateTime, nullable=True)
    interview_date = Column(DateTime, nullable=True)

    # 🚀 Zaman fonksiyonları güncellendi (Lambda kullanılarak anlık zaman garantilendi)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    
    # 🚀 İlan silinirse, o ilana yazılmış ön taslak mektuplar da silinir (Cascade)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    content = Column(Text, nullable=False)             # Motivasyon mektubu metni
    version = Column(Integer, default=1)               # Revizyon numarası
    is_approved = Column(Boolean, default=False)

    # AI metadata
    ai_model = Column(String(100), nullable=True)
    prompt_used = Column(Text, nullable=True)          # Debug için

    # 🚀 Zaman fonksiyonu güncellendi
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))