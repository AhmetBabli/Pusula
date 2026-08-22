from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import asyncio
import logging
import re

from backend.database import get_db, SessionLocal # SessionLocal arka plan için eklendi
from backend.models.inbox import EmailAccount, InboxItem
from backend.models.job import Job
from backend.models.user import UserProfile
from backend.automation.gmail_service import GmailService
from backend.automation.outreach_agent import OutreachAgent
from backend.ai.email_agent import EmailIntelligenceAgent
from backend.auth import get_current_user

router = APIRouter(prefix="/inbox", tags=["Inbox"])
logger = logging.getLogger(__name__)

# ── Pydantic Models ──

class AccountCreate(BaseModel):
    email: EmailStr  # str yerine EmailStr kullanıldı (Otomatik format doğrulaması)
    app_password: str

class AccountOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True

class InboxItemOut(BaseModel):
    id: int
    item_type: str
    title: str
    sender: str
    body_summary: str
    content_original: Optional[str] = None
    received_at: datetime
    is_read: bool
    is_applied: bool

    class Config:
        from_attributes = True

# ── Endpoints ──

@router.post("/accounts", response_model=AccountOut)
def add_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Link a new Gmail account. Password is encrypted automatically."""
    db_account = db.query(EmailAccount).filter(EmailAccount.email == account.email).first()
    if db_account:
        if db_account.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi başka bir hesaba bağlı.")
        db_account.app_password = account.app_password
        db_account.is_active = True
    else:
        db_account = EmailAccount(
            user_id=current_user.id,
            email=account.email,
            app_password=account.app_password  # Encrypted via property setter
        )
        db.add(db_account)

    db.commit()
    db.refresh(db_account)
    return db_account

@router.get("/accounts", response_model=List[AccountOut])
def get_accounts(db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """List the current user's linked accounts (passwords never exposed)."""
    return db.query(EmailAccount).filter(EmailAccount.user_id == current_user.id).all()

@router.get("/items", response_model=List[InboxItemOut])
def get_inbox_items(db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """List the current user's career items found by the AI agent."""
    items = (
        db.query(InboxItem)
        .join(EmailAccount, InboxItem.account_id == EmailAccount.id)
        .filter(EmailAccount.user_id == current_user.id)
        .order_by(InboxItem.received_at.desc())
        .all()
    )
    return items

def _get_own_item_or_404(db: Session, item_id: int, current_user: UserProfile) -> InboxItem:
    item = (
        db.query(InboxItem)
        .join(EmailAccount, InboxItem.account_id == EmailAccount.id)
        .filter(InboxItem.id == item_id, EmailAccount.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Öğe bulunamadı")
    return item

def _company_from_sender(sender: str) -> str:
    """'Ad Soyad <mail@sirket.com>' → 'Ad Soyad'; sadece e-posta ise domain'in ilk parçası."""
    named = re.match(r'^\s*"?([^"<]+?)"?\s*<', sender)
    if named and named.group(1).strip():
        return named.group(1).strip()
    domain = re.search(r'@([\w.-]+)', sender)
    if domain:
        return domain.group(1).split('.')[0].capitalize()
    return sender.strip() or "Bilinmeyen Gönderen"

@router.patch("/items/{item_id}/read", response_model=InboxItemOut)
def mark_item_read(item_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Öğeyi okundu olarak işaretle."""
    item = _get_own_item_or_404(db, item_id, current_user)
    item.is_read = True
    db.commit()
    db.refresh(item)
    return item

@router.post("/items/{item_id}/convert-to-job")
def convert_item_to_job(item_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Gelen kutusunda tespit edilen bir iş fırsatını takip edilebilir bir
    ilana dönüştürür. Gerçek bir ilan sayfası yok — bu yüzden source_url
    sentetik ama benzersiz (`inbox://item/{id}`), gerçek bir link gibi
    sunulmuyor. Dönüş değeri job_id: frontend bunu doğrudan mevcut
    POST /applications/prepare akışına yollayarak aynı mektup+e-posta
    keşfi pipeline'ını sıfırdan koda gerek kalmadan yeniden kullanıyor."""
    item = _get_own_item_or_404(db, item_id, current_user)
    if item.item_type != "job":
        raise HTTPException(status_code=400, detail="Sadece 'iş fırsatı' tipi öğeler başvuruya dönüştürülebilir.")

    job = Job(
        owner_user_id=current_user.id,
        source="gmail_inbox",
        source_url=f"inbox://item/{item.id}",
        title=item.title,
        company=_company_from_sender(item.sender),
        description=item.content_original or item.body_summary or "",
    )
    db.add(job)
    item.is_applied = True
    db.commit()
    db.refresh(job)
    return {"job_id": job.id}

@router.post("/sync", status_code=202)
async def sync_inbox(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Trigger the Gmail intelligence sync process for the current user's accounts."""
    accounts = db.query(EmailAccount).filter(
        EmailAccount.user_id == current_user.id, EmailAccount.is_active == True
    ).all()
    if not accounts:
        raise HTTPException(status_code=400, detail="Önce bir Gmail hesabı bağlamalısın.")
    
    # DB objelerini arka plana doğrudan yollayamayız! Session kapanır.
    # Bu yüzden sadece ihtiyaç olan verileri (id, email, pass) basit sözlüklere (dict) çeviriyoruz.
    accounts_data = [
        {
            "id": acc.id,
            "email": acc.email,
            "app_password": acc.app_password,
            "auth_method": acc.auth_method,
            "oauth_refresh_token": acc.oauth_refresh_token,
        }
        for acc in accounts
    ]
    
    # İşlemi arka plana devret ve hemen cevap dön
    background_tasks.add_task(run_sync_background, accounts_data, current_user.gemini_api_key)
    
    return {
        "status": "processing", 
        "message": "E-posta senkronizasyonu arka planda başlatıldı. AI analizleri tamamlandıkça sonuçlar düşecektir."
    }

# ── Arka Plan Görevi (Sync Logic) ──

async def run_sync_background(accounts_data: list, api_key: str = ""):
    """Fetch and analyze emails from linked accounts in the background."""
    
    # Arka plan görevi API'den koptuğu için kendi DB session'ını açar
    with SessionLocal() as db:
        for acc_data in accounts_data:
            logger.info(f"[Inbox] Syncing account: {acc_data['email']}")
            service = None
            try:
                if acc_data.get("auth_method") == "oauth":
                    # OAuth ile bağlı hesaplarda uygulama şifresi yok — IMAP yerine
                    # Gmail API'yi kısa ömürlü bir access_token ile kullanıyoruz.
                    access_token = OutreachAgent.refresh_google_access_token(acc_data.get("oauth_refresh_token"))
                    if not access_token:
                        logger.error(
                            f"[-] OAuth access token yenilenemedi ({acc_data['email']}) — "
                            "gmail.readonly izni verilmemiş olabilir, hesabı yeniden bağlayın."
                        )
                        continue
                    emails = await asyncio.to_thread(GmailService.fetch_via_gmail_api, access_token, 20)
                else:
                    service = GmailService(acc_data["email"], acc_data["app_password"])
                    # Ağır I/O işlemlerini threadpool'a yolluyoruz (sunucu kilitlenmesin diye)
                    is_connected = await asyncio.to_thread(service.connect)
                    if not is_connected:
                        logger.error(f"[-] Gmail connection failed for {acc_data['email']}")
                        continue
                    emails = await asyncio.to_thread(service.fetch_latest_emails, limit=20)

                logger.info(f"[Inbox] Fetched {len(emails)} emails from {acc_data['email']}")

                new_count = 0
                for mail_data in emails:
                    # Daha önce işlenmiş mi kontrol et (uid yalnızca aynı hesap içinde benzersiz)
                    existing = db.query(InboxItem).filter(
                        InboxItem.account_id == acc_data["id"], InboxItem.uid == mail_data["uid"]
                    ).first()
                    if existing:
                        continue
                        
                    # AI ile Analiz (Bu işlem asenkron olduğu için kendi yapısında kalabilir)
                    try:
                        intelligence = await EmailIntelligenceAgent.process_email(
                            mail_data["subject"],
                            mail_data["sender"],
                            mail_data["body"],
                            api_key=api_key,
                        )
                        
                        if intelligence:
                            new_item = InboxItem(
                                account_id=acc_data["id"],
                                uid=mail_data["uid"],
                                item_type=intelligence.get("type", "unknown"),
                                title=intelligence.get("title", "Başlıksız"),
                                sender=mail_data["sender"],
                                body_summary=intelligence.get("summary", ""),
                                content_original=mail_data["body"],
                                received_at=mail_data["received_at"]
                            )
                            db.add(new_item)
                            new_count += 1
                    except Exception as e:
                        logger.error(f"[-] AI processing error for email '{mail_data['subject'][:50]}': {e}")
                        continue
                
                # DB yazma işlemini onayla
                db.commit()
                logger.info(f"[Inbox] Added {new_count} new career items from {acc_data['email']}")
                
                # Bağlantıyı kapat (yalnızca IMAP yolunda bir bağlantı açıldıysa)
                if service is not None:
                    await asyncio.to_thread(service.disconnect)
                
            except Exception as e:
                db.rollback()
                logger.error(f"[-] Error syncing account {acc_data['email']}: {str(e)}", exc_info=True)
                continue