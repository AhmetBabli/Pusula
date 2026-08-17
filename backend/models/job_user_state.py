from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from backend.database import Base


class JobUserState(Base):
    """Bir ilanın BİR kullanıcı için durumu (favori, başvuru durumu, CV eşleşme
    skoru). Job satırı tüm kullanıcılar arasında paylaşılan ortak bir katalog
    olduğu için bu alanlar Job'da tutulamaz — iki kullanıcı aynı ilanı
    favorileyip başvurunca birbirinin durumunu ezerdi."""

    __tablename__ = "job_user_states"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(30), default="new")
    # new → reviewed → applying → applied → interview → offer → rejected

    is_favorite = Column(Boolean, default=False)

    # AI Eşleştirme (bu kullanıcının CV'sine göre)
    match_score = Column(Float, default=0.0)
    match_explanation = Column(Text, nullable=True)
    best_cv_id = Column(Integer, nullable=True)
    missing_skills = Column(JSON, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="_user_job_uc"),
    )
