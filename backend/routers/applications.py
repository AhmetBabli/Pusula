from datetime import datetime, timezone, timedelta
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
from backend.utils.db_helpers import get_or_create_job_state

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

class SendFollowupRequest(BaseModel):
    body: str = Field(..., min_length=10)

class OutcomeRequest(BaseModel):
    # Kullanıcının bildirdiği gerçek sonuç — CV performans analitiğini ve
    # takip nudge'ını gerçek anlamlı veriye kavuşturur.
    outcome: str = Field(..., pattern="^(interview|offer|rejected)$")

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
    contact_email_source_url: Optional[str] = None
    send_status: Optional[str] = None
    send_error: Optional[str] = None
    qa_answers: Optional[List[dict]] = None
    referral_candidates: Optional[List[dict]] = None
    followup_eligible: bool = False

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

    # Takip nudge'ı için eşik: gerçekten gönderilmiş (sent), henüz yanıt
    # gelmemiş, henüz takip e-postası da gönderilmemiş başvurularda 10+ gün
    # geçtiyse "takip e-postası öner" — tarih matematiğini burada yapıp
    # frontend'e hazır bir bool olarak veriyoruz.
    followup_threshold = datetime.now(timezone.utc) - timedelta(days=10)

    # Veritabanına tekrar gitmiyoruz, zaten çekilmiş verileri eşliyoruz
    for app, job, cv, cover in records:
        preview = None
        if cover and cover.content:
            preview = cover.content[:200] + "..." if len(cover.content) > 200 else cover.content

        submitted_at = app.submitted_at
        if submitted_at and submitted_at.tzinfo is None:
            submitted_at = submitted_at.replace(tzinfo=timezone.utc)
        followup_eligible = bool(
            app.send_status == "sent"
            and app.response_at is None
            and app.followup_sent_at is None
            and submitted_at and submitted_at < followup_threshold
        )

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
            "contact_email_source_url": app.contact_email_source_url,
            "send_status": app.send_status,
            "send_error": app.send_error,
            "qa_answers": app.qa_answers,
            "referral_candidates": app.referral_candidates,
            "followup_eligible": followup_eligible,
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
    job_state = get_or_create_job_state(db, current_user.id, job.id)
    if req.cv_id:
        cv = cv_query.filter(CV.id == req.cv_id).first()
    elif job_state.best_cv_id:
        cv = cv_query.filter(CV.id == job_state.best_cv_id).first()
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
    letter_content, (contact_email, contact_email_source, contact_email_source_url) = await asyncio.gather(
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
        contact_email_source_url=contact_email_source_url or None,
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
        "contact_email_source_url": application.contact_email_source_url,
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
            get_or_create_job_state(db, current_user.id, job.id).status = "applying"
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
                get_or_create_job_state(db, current_user.id, job.id).status = "applied"
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
        get_or_create_job_state(db, current_user.id, job.id).status = "applied"
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


@router.post("/{app_id}/find-referrals")
@limiter.limit("20/hour")
async def find_referrals(
    request: Request,
    app_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Hedef şirkette aynı üniversiteden mezun kişileri arar, her biri için
    LinkedIn'de doğrulanabilecek bir arama ipucu + kısa bir referans-isteme
    mesajı taslağı üretir. Sonuç tekrar Gemini çağırmamak için Application'a
    yazılır. LinkedIn API erişimimiz olmadığı için mesaj gönderilmiyor —
    kullanıcı LinkedIn'de kendisi bulup kopyala-yapıştır yapıyor."""
    from backend.ai.gemini_client import find_alumni_referrals

    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    if not job:
        raise HTTPException(status_code=400, detail="Başvuruya ait ilan bulunamadı")
    if not current_user.university:
        raise HTTPException(status_code=400, detail="Bu özellik için profilinizde üniversite bilgisi gerekli.")

    candidates = await find_alumni_referrals(
        company_name=job.company,
        university=current_user.university,
        target_role=job.title,
        user_name=current_user.full_name,
        api_key=current_user.gemini_api_key,
    )

    app.referral_candidates = candidates
    db.commit()
    db.refresh(app)

    return {"referral_candidates": app.referral_candidates}


@router.post("/{app_id}/draft-followup")
@limiter.limit("20/hour")
async def draft_followup(
    request: Request,
    app_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Gönderilmiş ama yanıt gelmemiş bir başvuru için takip e-postası
    taslağı üretir (kaydetmez — kullanıcı düzenleyip /send-followup ile
    gönderir, tıpkı ilk başvuru mektubu gibi onay öncesi son hali görülür)."""
    from backend.ai.gemini_client import generate_followup_email

    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    if not app.contact_email or app.send_status != "sent":
        raise HTTPException(status_code=400, detail="Bu başvuru için gerçek bir e-posta gönderimi yapılmamış.")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    submitted_at = app.submitted_at
    if submitted_at and submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=timezone.utc)
    days_since = (datetime.now(timezone.utc) - submitted_at).days if submitted_at else 0

    draft = await generate_followup_email(
        job_title=job.title if job else "",
        company_name=job.company if job else "",
        days_since_submitted=days_since,
        user_name=current_user.full_name,
        api_key=current_user.gemini_api_key,
    )

    if not draft:
        raise HTTPException(status_code=502, detail="Takip e-postası üretilemedi, lütfen tekrar deneyin.")

    return {"draft": draft, "contact_email": app.contact_email}


@router.post("/{app_id}/send-followup")
@limiter.limit("10/hour")
def send_followup(
    request: Request,
    app_id: int,
    req: SendFollowupRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Kullanıcının gördüğü/düzenlediği takip e-postasını gerçekten gönderir
    — submit_application'daki gerçek gönderimle aynı disiplin: onay sonrası,
    açık bir 'gönder' adımı."""
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    if not app.contact_email or app.send_status != "sent":
        raise HTTPException(status_code=400, detail="Bu başvuru için gerçek bir e-posta gönderimi yapılmamış.")

    account = db.query(EmailAccount).filter(
        EmailAccount.user_id == current_user.id, EmailAccount.is_active == True
    ).first()
    if not account:
        raise HTTPException(status_code=400, detail="Önce bir Gmail hesabı bağlamalısınız.")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    subject = f"Re: Başvuru - {job.title}" if job else "Re: Başvuru"
    html_body = req.body.replace("\n", "<br>")

    success = OutreachAgent.send_via_account(
        account=account,
        target_email=app.contact_email,
        subject=subject,
        html_body=html_body,
    )

    if not success:
        raise HTTPException(status_code=502, detail="Takip e-postası gönderilemedi. Lütfen tekrar deneyin.")

    app.followup_sent_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Takip e-postası {app.contact_email} adresine gönderildi. ✅", "followup_sent_at": app.followup_sent_at.isoformat()}


@router.post("/{app_id}/mark-responded")
def mark_responded(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Kullanıcı bu başvuruya (başka bir kanaldan da olsa) yanıt aldığını
    belirtir — takip nudge'ı bir daha önerilmez."""
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")

    app.response_at = datetime.now(timezone.utc)
    db.commit()

    return {"response_at": app.response_at.isoformat()}


@router.patch("/{app_id}/outcome")
def update_outcome(
    app_id: int,
    req: OutcomeRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Kullanıcının gerçek başvuru sonucunu (mülakat/teklif/red) kaydeder.
    Bu, CV varyant performans analitiğini eşleşme skoru gibi zayıf bir
    vekil yerine gerçek sonuçlara dayandırır, ve bir yanıt geldiğini
    ima ettiği için takip nudge'ını da otomatik susturur (response_at)."""
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    if app.status not in ("submitted", "interview", "offer"):
        raise HTTPException(status_code=400, detail="Sonuç sadece gönderilmiş bir başvuru için işaretlenebilir.")

    app.status = req.outcome
    if app.response_at is None:
        app.response_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": app.status, "response_at": app.response_at.isoformat()}