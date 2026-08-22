from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.database import Base

class OutreachRequest(Base):
    __tablename__ = "outreach_requests"

    id = Column(Integer, primary_key=True, index=True)

    # Sahibi: kullanıcı silinirse taslakları da silinir (Cascade)
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    company_name = Column(String(300), nullable=False)
    target_email = Column(String(300), nullable=False)
    subject = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)

    # awaiting_approval → sent | failed
    status = Column(String(20), default="awaiting_approval", nullable=False, index=True)
    send_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    submitted_at = Column(DateTime, nullable=True)
