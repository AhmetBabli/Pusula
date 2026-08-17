from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import UserProfile
from backend.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/users", tags=["Users"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None
    graduation_year: Optional[int] = None
    target_sectors: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    summary: Optional[str] = None
    onboarding_completed: Optional[bool] = None
    gemini_api_key: Optional[str] = None

# Not: hashed_password kasıtlı olarak dışarıda bırakıldı — asla API yanıtına sızmamalı.
class UserProfileOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None
    graduation_year: Optional[int] = None
    target_sectors: List[str] = []
    skills: List[str] = []
    languages: List[str] = []
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    summary: Optional[str] = None
    onboarding_completed: bool = False
    has_gemini_api_key: bool = False

    class Config:
        from_attributes = True

@router.get("/profile", response_model=UserProfileOut)
def get_profile(current_user: UserProfile = Depends(get_current_user)):
    return current_user

@router.patch("/profile")
def update_profile(
    data: ProfileUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return {"message": "Profil güncellendi"}
