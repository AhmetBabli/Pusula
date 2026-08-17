from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.config import settings
from backend.database import get_db
from backend.models.application import Application, CoverLetter
from backend.models.job import Job
from backend.models.cv import CV
from backend.models.user import UserProfile
from backend.models.inbox import EmailAccount
from backend.automation.outreach_agent import OutreachAgent
from backend.auth import get_current_user
from backend.rate_limiter import limiter

router = APIRouter(prefix="/applications", tags=["Başvurular"])

# === Pydantic Schemas ===

class CreateApplicationRequest(BaseModel):
    job_id: int
    cv_id: Optional[int] = None

class ApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None
    contact_email: Optional[str] = None  # Kullanıcı bulunan e-postayı onaydan önce düzeltebilir

class CustomQARequest(BaseModel):
    # Kullanıcının, ilanın kendi başvuru formunda gördüğü gerçek sorular
    questions: List[str] = Field(..., min_length=1, max_length=10)

# GET / listelemesi için alt şemalar
class JobSummary(BaseModel):
    id: int
    title: str
    company: str
    source_url: Optional[str] = None

class CVSummary(BaseModel):
    id: int
    title: str
    file_path: Optional[str] = None

class ApplicationOut(BaseModel):
    id: int
    status: str
    job: Optional[JobSummary]
    cv: Optional[CVSummary]
    cover_letter_preview: Optional[str]
    cover_letter_full: Optional[str] = None
    created_at: Optional[datetime]
    submitted_at: Optional[datetime]
    contact_email: Optional[str] = None
    contact_email_source: Optional[str] = None
    send_status: Optional[str] = None
    send_error: Optional[str] = None
    qa_answers: Optional[List[dict]] = None

# === Endpoints ===

@router.get("/", response_model=List[ApplicationOut])
def list_applications(
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Kullanıcının kendi başvurularını listele. N+1 problemi olmadan tek sorguda verileri çeker."""

    # Tüm tabloları tek bir sorguda (LEFT OUTER JOIN ile) birleştiriyoruz
    q = (
        db.query(Application, Job, CV, CoverLetter)
        .outerjoin(Job, Application.job_id == Job.id)
        .outerjoin(CV, Application.cv_id == CV.id)
        .outerjoin(CoverLetter, Application.cover_letter_id == CoverLetter.id)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
    )

    if status:
        q = q.filter(Application.status == status)

    records = q.all()
    result = []
    
    # Veritabanına tekrar gitmiyoruz, zaten çekilmiş verileri eşliyoruz
    for app, job, cv, cover in records:
        preview = None
        if cover and cover.content:
            preview = cover.content[:200] + "..." if len(cover.content) > 200 else cover.content
            
        result.append({
            "id": app.id,
            "status": app.status,
            "job": {"id": job.id, "title": job.title, "company": job.company, "source_url": job.source_url} if job else None,
            "cv": {"id": cv.id, "title": cv.title, "file_path": cv.file_path} if cv else None,
            "cover_letter_preview": preview,
            "cover_letter_full": cover.content if cover else None,
            "created_at": app.created_at,
            "submitted_at": app.submitted_at,
            "contact_email": app.contact_email,
            "contact_email_source": app.contact_email_source,
            "send_status": app.send_status,
            "send_error": app.send_error,
            "qa_answers": app.qa_answers,
        })
        
    return result

@router.post("/prepare")
@limiter.limit("20/hour")
async def prepare_application(
    request: Request,
    req: CreateApplicationRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """İlan için başvuru hazırla: CV seç + motivasyon mektubu üret + e-posta ara.
    Soru-cevap burada ÜRETİLMEZ — sitenin kendi formunda hangi soruların
    sorulacağını önceden bilemediğimiz için genel-geçer 5 soruyu tahmin edip
    boşuna bir AI çağrısı harcamak yerine, kullanıcı gerçek soruları görüp
    getirdiğinde /answer-questions ile anında cevaplıyoruz."""
    import asyncio
    from backend.ai.gemini_client import generate_cover_letter

    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="İlan bulunamadı")

    # CV Seçimi (yalnızca kendi CV'leri arasından)
    cv_query = db.query(CV).filter(CV.user_id == current_user.id)
    if req.cv_id:
        cv = cv_query.filter(CV.id == req.cv_id).first()
    elif job.best_cv_id:
        cv = cv_query.filter(CV.id == job.best_cv_id).first()
    else:
        cv = cv_query.filter(CV.is_default == True).first()

    if not cv:
        raise HTTPException(status_code=400, detail="Başvuru için CV gerekli. Lütfen önce CV yükleyin.")

    user_name = current_user.full_name
    university = current_user.university
    department = current_user.department

    # AI çağrılarını paralel çalıştırıyoruz (mektup + e-posta keşfi) — sırayla
    # çalıştırılsaydı kullanıcı ikisinin toplam süresi kadar beklerdi.
    # Not: Bu senkron bekliyor (API'yi bloklar), ancak kullanıcı direkt sonucu
    # görüp onaylayacağı için burada BackgroundTasks yerine bekletmek kabul edilebilir.
    letter_content, (contact_email, contact_email_source) = await asyncio.gather(
        generate_cover_letter(
            job_title=job.title,
            company_name=job.company,
            job_description=job.description or "",
            cv_text=cv.extracted_text or "",
            user_name=user_name,
            university=university,
            department=department,
            api_key=current_user.gemini_api_key,
        ),
        OutreachAgent.find_job_contact_email(job, api_key=current_user.gemini_api_key),
    )

    cover_letter = CoverLetter(
        job_id=job.id,
        content=letter_content,
        ai_model=settings.GEMINI_MODEL,
    )
    db.add(cover_letter)
    db.flush()

    application = Application(
        user_id=current_user.id,
        job_id=job.id,
        cv_id=cv.id,
        cover_letter_id=cover_letter.id,
        status="awaiting_approval",
        contact_email=contact_email or None,
        contact_email_source=contact_email_source or None,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "application_id": application.id,
        "status": "awaiting_approval",
        "job": {"title": job.title, "company": job.company},
        "cv_used": cv.title,
        "cover_letter": letter_content,
        "contact_email": application.contact_email,
        "contact_email_source": application.contact_email_source,
        "message": "Başvuru hazır! Onayınızı bekliyorum. 🎯",
    }

@router.post("/{app_id}/approve")
def approve_application(
    app_id: int,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Başvuruyu onayla veya reddet."""
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")

    if req.approved:
        app.status = "approved"
        app.notes = req.notes

        if req.contact_email is not None:
            # Kullanıcı bulunan/tahmin edilen e-postayı elle düzeltti
            app.contact_email = req.contact_email.strip() or None
            app.contact_email_source = "manual" if app.contact_email else None

        job = db.query(Job).filter(Job.id == app.job_id).first()
        if job:
            job.status = "applying"
    else:
        app.status = "draft"
        app.rejection_reason = req.notes

    db.commit()

    if req.approved:
        return {"message": "Başvuru onaylandı! Gönderime hazır. ✅", "status": "approved"}
    else:
        return {"message": "Başvuru reddedildi. Düzenleyebilirsiniz.", "status": "draft"}

@router.post("/{app_id}/answer-questions")
@limiter.limit("20/hour")
async def answer_custom_questions(
    request: Request,
    app_id: int,
    req: CustomQARequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Kullanıcının ilanın kendi başvuru formunda gördüğü gerçek soruları
    yanıtlar. Sitenin formunu otomatik okumaya çalışmıyoruz (kırılgan/güvensiz)
    — kullanıcı soruları kendi gözüyle görüp buraya yapıştırıyor, biz CV+ilana
    göre anında kopyala-yapıştıra hazır cevap üretiyoruz. Yeni cevaplar mevcut
    (genel) soru-cevap listesinin üzerine eklenir, üzerine yazmaz."""
    from backend.ai.gemini_client import generate_application_qa

    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    cv = db.query(CV).filter(CV.id == app.cv_id).first()
    if not job or not cv:
        raise HTTPException(status_code=400, detail="Başvuruya ait ilan veya CV bulunamadı")

    new_answers = await generate_application_qa(
        job_title=job.title,
        company_name=job.company,
        job_description=job.description or "",
        cv_text=cv.extracted_text or "",
        user_name=current_user.full_name,
        university=current_user.university,
        department=current_user.department,
        api_key=current_user.gemini_api_key,
        custom_questions=req.questions,
    )

    if not new_answers:
        raise HTTPException(status_code=502, detail="Cevaplar üretilemedi, lütfen tekrar deneyin.")

    app.qa_answers = (app.qa_answers or []) + new_answers
    db.commit()
    db.refresh(app)

    return {"qa_answers": app.qa_answers}

@router.post("/{app_id}/submit")
@limiter.limit("10/hour")
def submit_application(
    request: Request,
    app_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Onaylanmış başvuruyu gönder. Güvenilir bir e-posta bulunduysa gerçekten
    SMTP ile gönderir; bulunamadıysa bugünkü kopyala-yapıştır paketine düşer."""
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    if app.status != "approved":
        raise HTTPException(status_code=400, detail="Başvuru henüz onaylanmadı")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    cv = db.query(CV).filter(CV.id == app.cv_id).first()
    cover = db.query(CoverLetter).filter(CoverLetter.id == app.cover_letter_id).first()

    if app.contact_email:
        account = db.query(EmailAccount).filter(
            EmailAccount.user_id == current_user.id, EmailAccount.is_active == True
        ).first()
        if not account:
            raise HTTPException(
                status_code=400,
                detail="E-posta ile göndermek için önce bir Gmail hesabı bağlamalısınız (Google ile giriş yaparken izin vererek ya da Gelen Kutusu sekmesinden).",
            )

        subject = f"Başvuru: {job.title} - {current_user.full_name}" if job else f"Başvuru - {current_user.full_name}"
        html_body = (cover.content if cover else "").replace("\n", "<br>")

        success = OutreachAgent.send_via_account(
            account=account,
            target_email=app.contact_email,
            subject=subject,
            html_body=html_body,
            cv_path=cv.file_path if cv else None,
            cv_filename=cv.title if cv else None,
        )

        if success:
            app.status = "submitted"
            app.submitted_at = datetime.now(timezone.utc)
            app.send_status = "sent"
            app.send_error = None
            if job:
                job.status = "applied"
            db.commit()
            return {
                "message": f"Başvuru {app.contact_email} adresine gönderildi. ✅",
                "submitted_at": app.submitted_at.isoformat(),
                "send_status": "sent",
                "contact_email": app.contact_email,
            }
        else:
            app.send_status = "failed"
            app.send_error = "SMTP gönderimi başarısız oldu. Gmail hesabınızı ve uygulama şifresini kontrol edip tekrar deneyin."
            db.commit()
            raise HTTPException(status_code=502, detail=app.send_error)

    # E-posta bulunamadı: bugünkü kopyala-yapıştır davranışı aynen korunur
    app.status = "submitted"
    app.submitted_at = datetime.now(timezone.utc)
    app.send_status = "not_applicable"
    if job:
        job.status = "applied"
    db.commit()

    return {
        "message": "Copilot Modu Başlatıldı! 🚀",
        "submitted_at": app.submitted_at.isoformat(),
        "send_status": "not_applicable",
        "copilot_data": {
            "job_url": job.source_url if job else "",
            "cover_letter": cover.content if cover else "",
            "cv_path": cv.file_path if cv else ""
        }
    }