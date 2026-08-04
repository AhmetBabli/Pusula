"""
✅ Pydantic Validators for Input Validation
"""
from typing import List, Optional
from pydantic import BaseModel, field_validator, EmailStr


class CreateUserRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    university: str = "Doğuş Üniversitesi"
    department: str = "Yönetim Bilişim Sistemleri"
    graduation_year: Optional[int] = None
    target_sectors: List[str] = ["Yapay Zeka"]
    skills: List[str] = ["Python"]
    languages: List[str] = ["Türkçe"]
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Ad soyad en az 3 karakter olmalıdır")
        if len(v) > 200:
            raise ValueError("Ad soyad 200 karakterden uzun olamaz")
        return v.strip()
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not v.isdigit() and not any(c in v for c in ["+", "-", " ", "("]):
            raise ValueError("Telefon numarası geçersizdir")
        return v
    
    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(cls, v):
        from datetime import datetime
        if v is None:
            return v
        current_year = datetime.now().year
        if v < 2000 or v > current_year + 10:
            raise ValueError(f"Mezuniyet yılı {current_year - 50} ile {current_year + 10} arasında olmalıdır")
        return v
    
    @field_validator("target_sectors", "skills", "languages", mode="before")
    @classmethod
    def validate_lists(cls, v):
        if not isinstance(v, list):
            raise ValueError("Değer liste formatında olmalıdır")
        if len(v) == 0:
            raise ValueError("En az bir öğe seçilmelidir")
        if len(v) > 50:
            raise ValueError("Maksimum 50 öğe seçebilirsiniz")
        # Filter empty strings
        v = [item.strip() for item in v if isinstance(item, str) and item.strip()]
        return v


class UpdateApplicationRequest(BaseModel):
    status: str
    notes: Optional[str] = None
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["pending", "approved", "rejected", "submitted", "viewed"]
        if v not in valid_statuses:
            raise ValueError(f"Status {valid_statuses} arasından olmalıdır")
        return v
    
    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v):
        if v is None:
            return v
        if len(v) > 1000:
            raise ValueError("Notlar 1000 karakterden uzun olamaz")
        return v


class CreateCVRequest(BaseModel):
    title: str
    variant_type: str
    is_default: bool = False
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v or len(v) < 3:
            raise ValueError("CV başlığı en az 3 karakter olmalıdır")
        if len(v) > 200:
            raise ValueError("CV başlığı 200 karakterden uzun olamaz")
        return v.strip()
    
    @field_validator("variant_type")
    @classmethod
    def validate_variant(cls, v):
        valid_types = ["ai", "cyber", "it", "general"]
        if v not in valid_types:
            raise ValueError(f"Variant tipi {valid_types} arasından olmalıdır")
        return v
