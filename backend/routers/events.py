import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.database import get_db
from backend.models.event import Event
from backend.models.event_user_state import EventUserState
from backend.models.user import UserProfile
from backend.utils.db_helpers import get_or_404, get_or_create_event_state
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

    # is_online/is_free DB'de nullable değil ama Python-seviyesi default —
    # ALTER TABLE ile eklenmiş/elle düzenlenmiş bir satırda NULL kalabilir.
    # Tek bir NULL satır bu ucu kalıcı 500'e düşürmesin diye (bkz.
    # work_experiences/certificates'te yaşanan aynı sınıf bug), sütunun kendi
    # varsayılanına düşülüyor.
    @field_validator("is_online", mode="before")
    @classmethod
    def _none_to_false(cls, v):
        return v if v is not None else False

    @field_validator("is_free", mode="before")
    @classmethod
    def _none_to_true(cls, v):
        return v if v is not None else True

    class Config:
        from_attributes = True  # SQLAlchemy objesini Pydantic'e bağrar (dict veya ORM objesi kabul eder)

# === Yardımcılar ===

def _serialize_event(event: Event, state: Optional[EventUserState]) -> dict:
    """Event (paylaşılan katalog) ile EventUserState'i (bu kullanıcıya özel
    durum) tek bir yanıt sözlüğünde birleştirir — state yoksa varsayılan
    ('found') döner."""
    return {
        "id": event.id,
        "title": event.title,
        "organizer": event.organizer,
        "description": event.description,
        "event_type": event.event_type,
        "location": event.location,
        "is_online": event.is_online,
        "is_free": event.is_free,
        "event_date": event.event_date,
        "registration_deadline": event.registration_deadline,
        "relevance_score": event.relevance_score,
        "relevance_reason": event.relevance_reason,
        "status": state.status if state else "found",
        "notes": event.notes,
        "source": event.source,
        "source_url": event.source_url,
    }

# === Endpoints ===

@router.post("/", response_model=EventOut, status_code=201)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Manuel olarak yeni bir etkinlik ekler (Eksik olan endpoint eklendi)."""
    event_data = event_in.model_dump()
    # source_url unique+nullable=False — boş bırakılırsa (manuel eklemede
    # normal) ikinci manuel etkinlik IntegrityError ile 500 veriyordu.
    if not event_data.get("source_url"):
        event_data["source_url"] = f"manual://event/{uuid.uuid4()}"
    new_event = Event(**event_data)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return _serialize_event(new_event, None)

@router.get("/", response_model=List[EventOut])
def list_events(
    event_type: str = Query(None, description="Filtre: hackathon, career_fair, seminar, networking, workshop"),
    status: str = Query(None, description="Filtre: found, interested, registered, attended, skipped"),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Etkinlikleri listele. Etkinlikler tüm kullanıcılar arasında paylaşılan bir
    katalogdur; durum ise bu kullanıcıya özel (EventUserState) — LEFT JOIN ile,
    hiç etkileşilmemiş etkinlikler varsayılan değerle ("found") döner."""
    state_status = func.coalesce(EventUserState.status, "found")

    q = (
        db.query(Event, EventUserState)
        .outerjoin(
            EventUserState,
            (EventUserState.event_id == Event.id) & (EventUserState.user_id == current_user.id),
        )
        .order_by(Event.event_date.desc())
    )

    if event_type:
        q = q.filter(Event.event_type == event_type)
    if status:
        q = q.filter(state_status == status)

    rows = q.limit(100).all()
    return [_serialize_event(ev, state) for ev, state in rows]

@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Etkinlik detayı."""
    event = get_or_404(db, Event, event_id, "Etkinlik")
    state = db.query(EventUserState).filter(
        EventUserState.user_id == current_user.id, EventUserState.event_id == event_id
    ).first()
    return _serialize_event(event, state)

@router.patch("/{event_id}/status")
def update_event_status(
    event_id: int,
    payload: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Etkinlik durumunu JSON body üzerinden günceller — sadece bu kullanıcı için."""
    valid_statuses = ["found", "interested", "registered", "attended", "skipped"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Geçersiz durum. Geçerli: {valid_statuses}")

    get_or_404(db, Event, event_id, "Etkinlik")
    state = get_or_create_event_state(db, current_user.id, event_id)
    state.status = payload.status
    db.commit()

    return {"message": f"Etkinlik durumu '{payload.status}' olarak güncellendi"}