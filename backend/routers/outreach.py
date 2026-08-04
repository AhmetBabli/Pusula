from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging
import asyncio

from backend.database import get_db
from backend.models.user import UserProfile
from backend.models.cv import CV
from backend.models.inbox import EmailAccount
from backend.automation.outreach_agent import OutreachAgent
from backend.ai.gemini_client import generate_cold_email
from backend.auth import get_current_user

router = APIRouter(prefix="/outreach", tags=["Outreach"])
logger = logging.getLogger(__name__)

class ColdEmailRequest(BaseModel):
    company_name: str = Field(..., min_length=2, description="Hedef şirketin adı")

# ─── ARKA PLAN GÖREVİ (Ağır İşlemler Burada Yapılır) ───
async def process_outreach_task(
    company_name: str,
    user_name: str,
    university: str,
    department: str,
    cv_text: str,
    cv_path: str,
    sender_email: str,
    auth_method: str = "app_password",
    app_password: str = None,
    oauth_refresh_token: str = None,
):
    """
    Kullanıcıyı API'de bekletmemek için mail bulma, AI önyazı üretme ve 
    SMTP gönderim işlemlerini arka planda yürüten asıl fonksiyon.
    """
    logger.info(f"[{company_name}] için arka plan başvuru süreci başladı...")

    try:
        # 1. İstihbarat (Senkron fonksiyonu async içinde bloke etmeden çalıştırıyoruz)
        target_email = await asyncio.to_thread(OutreachAgent.hunt_email, company_name)
        if not target_email:
            logger.error(f"[{company_name}] için uygun İK e-postası bulunamadı. İşlem iptal.")
            return

        # 2. AI ile Önyazı Hazırla
        email_body = await generate_cold_email(
            company_name=company_name,
            cv_text=cv_text,
            user_name=user_name,
            university=university,
            department=department
        )
        html_body = email_body.replace("\n", "<br>")
        subject = f"Staj / Çalışma Başvurusu - {user_name} ({department})".strip()

        # 3. Gönderim İşlemi (Google OAuth ile bağlıysa Gmail API, değilse SMTP + uygulama şifresi)
        if auth_method == "oauth":
            access_token = await asyncio.to_thread(OutreachAgent.refresh_google_access_token, oauth_refresh_token)
            if not access_token:
                logger.error(f"[{company_name}] Google erişim token'ı alınamadı, gönderim iptal.")
                return
            success = await asyncio.to_thread(
                OutreachAgent.send_via_gmail_api,
                access_token,
                sender_email,
                target_email,
                subject,
                html_body,
                cv_path,
            )
        else:
            success = await asyncio.to_thread(
                OutreachAgent.send_cold_email,
                sender_email=sender_email,
                app_password=app_password,
                target_email=target_email,
                subject=subject,
                html_body=html_body,
                cv_path=cv_path
            )

        if success:
            logger.info(f"[{company_name}] şirketine soğuk başvuru ({target_email}) başarıyla iletildi!")
        else:
            logger.error(f"[{company_name}] e-posta gönderimi başarısız oldu.")

    except Exception as e:
        logger.error(f"[{company_name}] Arka plan işleminde kritik hata: {str(e)}")


# ─── API ENDPOINT (Sadece Doğrulama Yapar ve Hemen Cevap Döner) ───
@router.post("/cold-email", status_code=202)
async def send_cold_email(
    req: ColdEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Hedef şirket başvurusunu alır ve arka plan işlem kuyruğuna (Background Task) ekler.
    """
    # 1. Hızlı Veritabanı Kontrolleri (Bu kısımlar milisaniyeler sürer, kullanıcı bekleyebilir)
    cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.is_default.desc(), CV.id.desc()).first()
    if not cv or not cv.extracted_text:
        raise HTTPException(status_code=400, detail="Sistemde geçerli/okunabilir bir CV bulunamadı.")

    account = db.query(EmailAccount).filter(
        EmailAccount.user_id == current_user.id, EmailAccount.is_active == True
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Aktif bir e-posta hesabı bağlı değil.")

    # 2. Ağır İşlemi Arka Plana Devret
    # Dikkat: DB objelerini direkt arka plana göndermek yerine içindeki string verileri gönderiyoruz.
    # Böylece veritabanı session'ı kapansa bile arka plan işlemi verilerle çalışmaya devam edebilir.
    background_tasks.add_task(
        process_outreach_task,
        company_name=req.company_name,
        user_name=current_user.full_name,
        university=current_user.university,
        department=current_user.department or "Bölüm Belirtilmemiş",
        cv_text=cv.extracted_text,
        cv_path=cv.file_path,
        sender_email=account.email,
        auth_method=account.auth_method,
        app_password=account.app_password if account.auth_method != "oauth" else None,
        oauth_refresh_token=account.oauth_refresh_token if account.auth_method == "oauth" else None,
    )
    
    # 3. Anında Yanıt Dön (Timeout riskini ortadan kaldırdık)
    return {
        "status": "processing", 
        "message": f"'{req.company_name}' şirketi için başvuru hazırlığı arka plana alındı. Gelişmeler loglara yansıyacaktır."
    }