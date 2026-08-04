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