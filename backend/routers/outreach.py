from datetime import datetime, timezone
from typing import Optional
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.database import get_db
from backend.models.user import UserProfile
from backend.models.cv import CV
from backend.models.inbox import EmailAccount
from backend.models.outreach import OutreachRequest
from backend.automation.outreach_agent import OutreachAgent
from backend.ai.gemini_client import generate_cold_email
from backend.auth import get_current_user

router = APIRouter(prefix="/outreach", tags=["Outreach"])
logger = logging.getLogger(__name__)


class ColdEmailRequest(BaseModel):
    company_name: str = Field(..., min_length=2, description="Hedef şirketin adı")


class SendRequest(BaseModel):
    target_email: Optional[str] = None  # Kullanıcı e-postayı göndermeden önce düzeltebilir


class OutreachOut(BaseModel):
    id: int
    company_name: str
    target_email: str
    subject: str
    body: str
    status: str
    send_error: Optional[str] = None

    class Config:
        from_attributes = True


def _active_email_account(db: Session, user_id: int) -> EmailAccount:
    account = db.query(EmailAccount).filter(
        EmailAccount.user_id == user_id, EmailAccount.is_active == True
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Aktif bir e-posta hesabı bağlı değil.")
    return account


def _default_cv(db: Session, user_id: int) -> CV:
    cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.is_default.desc(), CV.id.desc()).first()
    if not cv or not cv.extracted_text:
        raise HTTPException(status_code=400, detail="Sistemde geçerli/okunabilir bir CV bulunamadı.")
    return cv


@router.post("/prepare", response_model=OutreachOut)
async def prepare_outreach(
    req: ColdEmailRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Soğuk e-postayı HAZIRLAR ama göndermez: hedef şirket için İK e-postasını bulur,
    AI ile taslak yazar ve kullanıcının onayına sunar. Onaylı Copilot ilkesi burada da
    geçerli — gönderim ayrı, açık bir adım (POST /outreach/{id}/send)."""
    cv = _default_cv(db, current_user.id)
    _active_email_account(db, current_user.id)  # yalnızca bağlı bir hesap olduğunu doğrula

    target_email = await OutreachAgent.hunt_email(req.company_name, api_key=current_user.gemini_api_key)
    if not target_email:
        raise HTTPException(
            status_code=404,
            detail=f"'{req.company_name}' için uygun bir İK/iletişim e-postası bulunamadı.",
        )

    department = current_user.department or "Bölüm Belirtilmemiş"
    email_body = await generate_cold_email(
        company_name=req.company_name,
        cv_text=cv.extracted_text,
        user_name=current_user.full_name,
        university=current_user.university or "",
        department=department,
        api_key=current_user.gemini_api_key,
    )
    subject = f"Staj / Çalışma Başvurusu - {current_user.full_name} ({department})".strip()

    draft = OutreachRequest(
        user_id=current_user.id,
        company_name=req.company_name,
        target_email=target_email,
        subject=subject,
        body=email_body,
        status="awaiting_approval",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{outreach_id}/send", response_model=OutreachOut)
async def send_outreach(
    outreach_id: int,
    req: SendRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Kullanıcı taslağı ve alıcıyı gördükten sonra AÇIKÇA onaylayıp gönderir.
    Bu, kullanıcının bilinçli olarak 'gönder' dediği tek an — hazırlık aşaması
    (prepare) hiçbir dış tarafa hiçbir şey göndermez."""
    draft = db.query(OutreachRequest).filter(
        OutreachRequest.id == outreach_id, OutreachRequest.user_id == current_user.id
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı.")
    if draft.status == "sent":
        raise HTTPException(status_code=400, detail="Bu e-posta zaten gönderildi.")

    if req.target_email is not None and req.target_email.strip():
        draft.target_email = req.target_email.strip()

    account = _active_email_account(db, current_user.id)
    cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.is_default.desc(), CV.id.desc()).first()
    html_body = draft.body.replace("\n", "<br>")

    success = await asyncio.to_thread(
        OutreachAgent.send_via_account,
        account=account,
        target_email=draft.target_email,
        subject=draft.subject,
        html_body=html_body,
        cv_path=cv.file_path if cv else None,
        cv_filename=cv.title if cv else None,
    )

    if success:
        draft.status = "sent"
        draft.send_error = None
        draft.submitted_at = datetime.now(timezone.utc)
        logger.info(f"[{draft.company_name}] soğuk başvuru ({draft.target_email}) onaylanıp gönderildi.")
    else:
        draft.status = "failed"
        draft.send_error = "Gönderim başarısız oldu. Gmail hesabınızı kontrol edip tekrar deneyin."

    db.commit()
    db.refresh(draft)

    if draft.status == "failed":
        raise HTTPException(status_code=502, detail=draft.send_error)
    return draft
