from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.database import get_db
from backend.models.event import Event
from backend.models.user import UserProfile
from backend.utils.db_helpers import get_or_404
from backend.auth import get_current_user

router = APIRouter(prefix="/events", tags=["Etkinlikler"])

# === Pydantic Schemas ===

# PATCH istekleri için JSON body şeması
class EventStatusUpdate(BaseModel):
    status: str

# POST istekleri için (str yerine datetime kullandık)
class EventCreate(BaseModel):
    title: str
    source: str = "manual"
    source_url: str = ""
    organizer: Optional[str] = None
    description: Optional[str] = None
    event_type: str = "seminar"   # hackathon, career_fair, seminar, networking, workshop
    location: Optional[str] = None
    is_online: bool = False
    is_free: bool = True
    event_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None

# GET istekleri için çıktı şeması (Veritabanı objesini otomatik JSON yapar)
class EventOut(BaseModel):
    id: int
    title: str
    organizer: Optional[str]
    description: Optional[str]
    event_type: str
    location: Optional[str]
    is_online: bool
    is_free: bool
    event_date: Optional[datetime]
    registration_deadline: Optional[datetime]
    relevance_score: Optional[float]
    relevance_reason: Optional[str]
    status: str
    notes: Optional[str]
    source: str
    source_url: Optional[str]

    class Config:
        from_attributes = True  # SQLAlchemy objesini Pydantic'e bağlar

# === Endpoints ===

@router.post("/", response_model=EventOut, status_code=201)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Manuel olarak yeni bir etkinlik ekler (Eksik olan endpoint eklendi)."""
    new_event = Event(**event_in.model_dump())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@router.get("/", response_model=List[EventOut])
def list_events(
    event_type: str = Query(None, description="Filtre: hackathon, career_fair, seminar, networking, workshop"),
    status: str = Query(None, description="Filtre: found, interested, registered, attended, skipped"),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Etkinlikleri listele. Etkinlikler tüm kullanıcılar arasında paylaşılan bir katalogdur."""
    q = db.query(Event).order_by(Event.event_date.desc())

    if event_type:
        q = q.filter(Event.event_type == event_type)
    if status:
        q = q.filter(Event.status == status)

    return q.limit(100).all()

@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Etkinlik detayı."""
    return get_or_404(db, Event, event_id, "Etkinlik")

@router.patch("/{event_id}/status")
def update_event_status(
    event_id: int,
    payload: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Etkinlik durumunu JSON body üzerinden güncelle."""
    valid_statuses = ["found", "interested", "registered", "attended", "skipped"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Geçersiz durum. Geçerli: {valid_statuses}")

    event = get_or_404(db, Event, event_id, "Etkinlik")
    event.status = payload.status
    db.commit()

    return {"message": f"Etkinlik durumu '{payload.status}' olarak güncellendi"}