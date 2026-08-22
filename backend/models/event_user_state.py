from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from backend.database import Base


class EventUserState(Base):
    """Bir etkinliğin BİR kullanıcı için durumu (ilgileniyorum/kayıtlı/katıldım).
    Event satırı tüm kullanıcılar arasında paylaşılan ortak bir katalog olduğu
    için status burada tutulamaz — JobUserState'in Job için çözdüğü sınıf
    hatanın aynısı: aksi halde herhangi bir kullanıcının PATCH'i herkesin
    durumunu ezerdi."""

    __tablename__ = "event_user_states"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(30), default="found")
    # found → interested → registered → attended → skipped

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="_user_event_uc"),
    )
