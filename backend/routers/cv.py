import os
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.database import get_db, SessionLocal
from backend.models.cv import CV
from backend.models.user import UserProfile
from backend.config import settings
from backend.utils.db_helpers import get_or_404
from backend.auth import get_current_user

router = APIRouter(prefix="/cvs", tags=["CV Yönetimi"])
logger = logging.getLogger(__name__)

# === Pydantic Schemas ===

class CVCreateRequest(BaseModel):
    title: str
    variant_type: str  # ai, cyber, it, general

class CVGenerateRequest(BaseModel):
    variant_type: str
    user_name: str = Field(default="Ahmet Babli", max_length=200)
    email: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=30)
    university: str = Field(default="Doğuş Üniversitesi", max_length=200)
    department: str = Field(default="Yönetim Bilişim Sistemleri", max_length=200)
    skills: list[str] = Field(default_factory=list)
    experience: str = Field(default="", max_length=8000)
    projects: str = Field(default="", max_length=8000)

# Çıktı şeması (Pydantic otomatik dönüştürecek)
class CVOut(BaseModel):
    id: int
    title: str
    variant_type: str
    extracted_text: Optional[str] = None
    ats_score: Optional[float] = 0.0
    ats_feedback: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    target_keywords: List[str] = Field(default_factory=list)
    is_default: bool = False
    is_ai_generated: bool = False
    file_path: Optional[str] = None

    # DB'de bu alanlar NULL olsa bile (ör. eski/elle eklenmiş kayıtlar) yanıt
    # şeması çökmesin — boş liste / False'a sessizce indirger. Daha önce tek bir
    # NULL satır GET /cvs/'in TÜM listeyi 500 ile çökertmesine yol açmıştı.
    @field_validator("strengths", "weaknesses", "target_keywords", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v):
        return v if v is not None else []

    @field_validator("is_default", "is_ai_generated", mode="before")
    @classmethod
    def _none_to_false(cls, v):
        return v if v is not None else False

    class Config:
        from_attributes = True


# === Yardımcı Arka Plan Fonksiyonları ===

def extract_pdf_text_sync(file_path: str) -> str:
    """PDF okuma işlemini thread içinde yapmak için senkron fonksiyon."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"[CV] PDF Okuma hatası: {e}")
        return ""

async def background_ats_analysis(cv_id: int, api_key: str = ""):
    """ATS analizini arka planda yaparak API'yi bekletmez."""
    from backend.ai.gemini_client import analyze_cv_ats

    with SessionLocal() as db:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv or not cv.extracted_text:
            return

        try:
            logger.info(f"[CV] {cv.title} için otonom AI analizi başladı...")
            result = await analyze_cv_ats(cv.extracted_text, api_key=api_key)
            
            cv.ats_score = result.get("score", 0)
            cv.ats_feedback = result.get("feedback", "")
            cv.strengths = result.get("strengths", [])
            cv.weaknesses = result.get("weaknesses", [])
            cv.target_keywords = result.get("keywords", [])
            
            db.commit()
            logger.info(f"[CV] AI Analizi tamamlandı. Skor: {cv.ats_score}")
        except Exception as e:
            db.rollback()
            logger.error(f"[-] [CV] AI analiz hatası: {e}")


# === Endpoints ===

@router.get("/", response_model=List[CVOut])
def list_cvs(db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Kullanıcının kendi CV'lerini listele."""
    return db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()

def _get_own_cv_or_404(db: Session, cv_id: int, current_user: UserProfile) -> CV:
    cv = get_or_404(db, CV, cv_id, "CV")
    if cv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="CV bulunamadı")
    return cv

@router.get("/{cv_id}", response_model=CVOut)
def get_cv(cv_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """CV detayını getir."""
    return _get_own_cv_or_404(db, cv_id, current_user)

@router.get("/{cv_id}/pdf")
def download_cv_pdf(cv_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """CV PDF'ini indir — sahiplik kontrolü _get_own_cv_or_404 ile yapılır.
    Eskiden /agents/cv/export-pdf/{session_id} istemcinin seçtiği bir
    session_id'ye göre dosya sunuyordu; herhangi bir kullanıcı başka birinin
    session_id'sini tahmin ederek onun CV'sini indirebiliyordu (IDOR)."""
    cv = _get_own_cv_or_404(db, cv_id, current_user)
    if not cv.file_path or not os.path.exists(cv.file_path):
        raise HTTPException(404, "Bu CV için PDF bulunamadı.")
    return FileResponse(
        path=cv.file_path,
        media_type="application/pdf",
        filename=f"kariyer_cv_{cv_id}.pdf",
    )

@router.post("/upload", status_code=202)
async def upload_cv(
    background_tasks: BackgroundTasks,
    title: str = Form(..., max_length=200),
    variant_type: str = Form(..., max_length=50),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """PDF CV yükle, metin çıkar ve AI analizini arka planda başlat."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir")

    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Geçersiz dosya tipi. Sadece PDF kabul edilir.")

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Dosya çok büyük. Maksimum 5 MB.")
    await file.seek(0)

    import re
    safe_variant = re.sub(r'[^a-zA-Z0-9_]', '', variant_type) or "general"

    # Dosya kaydetme
    os.makedirs(settings.CV_STORE_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_variant}_{timestamp}.pdf"
    file_path = str(settings.CV_STORE_PATH / filename)

    # I/O işlemi olduğu için await to_thread kullanmak daha sağlıklıdır ama basit write için tolere edilebilir.
    with open(file_path, "wb") as f:
        f.write(contents)

    # Ağır CPU işlemini arka plan iş parçacığına (thread) devret
    extracted_text = await asyncio.to_thread(extract_pdf_text_sync, file_path)

    cv = CV(
        user_id=current_user.id,
        title=title,
        variant_type=variant_type,
        file_path=file_path,
        extracted_text=extracted_text or None,
        is_ai_generated=False,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)

    # ATS Analizini Background Task'a atıyoruz. 
    # API anında cevap dönerken Gemini analizi arkada devam edecek.
    if extracted_text and len(extracted_text.strip()) > 50:
        background_tasks.add_task(background_ats_analysis, cv.id, current_user.gemini_api_key)

    return {
        "id": cv.id, 
        "title": cv.title, 
        "message": "CV başarıyla yüklendi. ATS analizi arka planda başlatıldı.", 
        "extracted_length": len(extracted_text)
    }

def _format_structured_experience(current_user: UserProfile) -> str:
    """Profildeki yapılandırılmış iş deneyimi/sertifika girdilerini (bkz.
    ProfileIntake/ProfileView'daki deneyim formu) CV üretim prompt'una
    eklenecek okunabilir bir metne çevirir."""
    parts = []
    if current_user.work_experiences:
        lines = ["İş Deneyimleri:"]
        for exp in current_user.work_experiences:
            period = f"{exp.get('start_date') or ''} - {'Devam ediyor' if exp.get('current') else (exp.get('end_date') or '')}"
            lines.append(f"- {exp.get('title', '')} @ {exp.get('company', '')} ({period.strip(' -')})")
            if exp.get('description'):
                lines.append(f"  {exp['description']}")
        parts.append("\n".join(lines))
    if current_user.certificates:
        lines = ["Sertifikalar:"]
        for cert in current_user.certificates:
            lines.append(f"- {cert.get('name', '')} — {cert.get('issuer', '')} ({cert.get('date', '')})")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


@router.post("/generate", response_model=CVOut)
async def generate_cv(
    req: CVGenerateRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """AI ile CV oluştur."""
    from backend.ai.gemini_client import generate_cv_content

    # Kullanıcı LinkedIn profilinden (Deneyim/Eğitim) kopyaladığı ham metni
    # profiline kaydettiyse, formda tekrar yazmasına gerek kalmadan otomatik
    # olarak deneyim bağlamına ekleniyor.
    experience = req.experience
    if current_user.linkedin_data:
        experience = f"{experience}\n\nLinkedIn Profilinden:\n{current_user.linkedin_data}".strip()
    structured = _format_structured_experience(current_user)
    if structured:
        experience = f"{experience}\n\n{structured}".strip()

    # Bu endpoint de yavaş çalışacaktır ancak kullanıcı bir şeyin "üretilmesini"
    # talep ettiği için burada beklemesi (progress bar ile) kabul edilebilir.
    content = await generate_cv_content(
        user_name=req.user_name,
        email=req.email,
        phone=req.phone,
        university=req.university,
        department=req.department,
        skills=req.skills,
        variant_type=req.variant_type,
        experience=experience,
        projects=req.projects,
        api_key=current_user.gemini_api_key,
    )

    variant_titles = {
        "ai": "AI & Veri Bilimi Odaklı CV",
        "cyber": "Siber Güvenlik Odaklı CV",
        "it": "IT & Sistem Yönetimi CV",
        "general": "Genel YBS CV",
    }

    cv = CV(
        user_id=current_user.id,
        title=variant_titles.get(req.variant_type, f"{req.variant_type} CV"),
        variant_type=req.variant_type,
        extracted_text=content,
        is_ai_generated=True,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)

    return cv

@router.post("/{cv_id}/ats-analyze", status_code=202)
async def ats_analyze(
    cv_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Manuel tetiklenen ATS analizini arka plana al."""
    cv = _get_own_cv_or_404(db, cv_id, current_user)
    if not cv.extracted_text:
        raise HTTPException(status_code=400, detail="CV metni bulunamadı")

    background_tasks.add_task(background_ats_analysis, cv.id, current_user.gemini_api_key)
    return {"message": "ATS analizi başlatıldı. Sonuçlar birazdan güncellenecek."}

@router.delete("/{cv_id}")
def delete_cv(cv_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """CV sil."""
    cv = _get_own_cv_or_404(db, cv_id, current_user)

    if cv.file_path and os.path.exists(cv.file_path):
        os.remove(cv.file_path)

    db.delete(cv)
    db.commit()
    return {"message": f"CV '{cv.title}' silindi"}

@router.patch("/{cv_id}/set-default")
def set_default_cv(cv_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Varsayılan CV olarak ayarla."""
    cv = _get_own_cv_or_404(db, cv_id, current_user)

    db.query(CV).filter(CV.user_id == current_user.id).update({"is_default": False})
    cv.is_default = True
    db.commit()
    return {"message": f"'{cv.title}' artık varsayılan CV"}