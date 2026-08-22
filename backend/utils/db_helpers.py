"""
Kariyer Ajanı — Database Helpers
"""
from typing import Type, TypeVar
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

# Gelişmiş otomatik tamamlama için Tip Değişkeni (Type Variable)
T = TypeVar("T")

def get_or_404(db: Session, model: Type[T], id: int, detail: str = None) -> T:
    """Belirtilen ID'ye göre kaydı getirir, yoksa 404 fırlatır."""

    # 🚀 YENİ: Modern SQLAlchemy 2.0 Sorgu Yapısı
    stmt = select(model).where(model.id == id)
    record = db.execute(stmt).scalar_one_or_none()

    if not record:
        name = detail or f"{model.__name__}"
        raise HTTPException(status_code=404, detail=f"{name} bulunamadı")

    return record


def get_or_create_job_state(db: Session, user_id: int, job_id: int):
    """Bir ilanın bu kullanıcı için durumunu (JobUserState) getirir, yoksa
    varsayılan değerlerle oluşturur. Job satırı tüm kullanıcılar arasında
    paylaşılan bir katalog olduğu için status/is_favorite/match_score gibi
    kullanıcıya özel alanlar orada değil, burada tutulur — jobs.py ve
    applications.py routers'ı bunu paylaşır."""
    from backend.models.job_user_state import JobUserState

    state = db.query(JobUserState).filter(
        JobUserState.user_id == user_id, JobUserState.job_id == job_id
    ).first()
    if not state:
        state = JobUserState(user_id=user_id, job_id=job_id)
        db.add(state)
        db.flush()
    return state


def get_or_create_event_state(db: Session, user_id: int, event_id: int):
    """Bir etkinliğin bu kullanıcı için durumunu (EventUserState) getirir, yoksa
    varsayılan değerlerle oluşturur — get_or_create_job_state ile aynı desen."""
    from backend.models.event_user_state import EventUserState

    state = db.query(EventUserState).filter(
        EventUserState.user_id == user_id, EventUserState.event_id == event_id
    ).first()
    if not state:
        state = EventUserState(user_id=user_id, event_id=event_id)
        db.add(state)
        db.flush()
    return state