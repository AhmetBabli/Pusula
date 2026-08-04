from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr
import asyncio
import logging

from backend.database import get_db, SessionLocal # SessionLocal arka plan için eklendi
from backend.models.inbox import EmailAccount, InboxItem
from backend.models.user import UserProfile
from backend.automation.gmail_service import GmailService
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
    received_at: str
    is_read: bool

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
        {"id": acc.id, "email": acc.email, "app_password": acc.app_password} 
        for acc in accounts
    ]
    
    # İşlemi arka plana devret ve hemen cevap dön
    background_tasks.add_task(run_sync_background, accounts_data)
    
    return {
        "status": "processing", 
        "message": "E-posta senkronizasyonu arka planda başlatıldı. AI analizleri tamamlandıkça sonuçlar düşecektir."
    }

# ── Arka Plan Görevi (Sync Logic) ──

async def run_sync_background(accounts_data: list):
    """Fetch and analyze emails from linked accounts in the background."""
    
    # Arka plan görevi API'den koptuğu için kendi DB session'ını açar
    with SessionLocal() as db:
        for acc_data in accounts_data:
            logger.info(f"[Inbox] Syncing account: {acc_data['email']}")
            try:
                service = GmailService(acc_data["email"], acc_data["app_password"])
                
                # Ağır I/O işlemlerini threadpool'a yolluyoruz (sunucu kilitlenmesin diye)
                is_connected = await asyncio.to_thread(service.connect)
                if not is_connected:
                    logger.error(f"[-] Gmail connection failed for {acc_data['email']}")
                    continue
                
                logger.info(f"[Inbox] Connected to {acc_data['email']}, fetching emails...")
                emails = await asyncio.to_thread(service.fetch_latest_emails, limit=20)
                logger.info(f"[Inbox] Fetched {len(emails)} emails from {acc_data['email']}")
                
                new_count = 0
                for mail_data in emails:
                    # Daha önce işlenmiş mi kontrol et
                    existing = db.query(InboxItem).filter(InboxItem.uid == mail_data["uid"]).first()
                    if existing:
                        continue
                        
                    # AI ile Analiz (Bu işlem asenkron olduğu için kendi yapısında kalabilir)
                    try:
                        intelligence = await EmailIntelligenceAgent.process_email(
                            mail_data["subject"],
                            mail_data["sender"],
                            mail_data["body"]
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
                
                # Bağlantıyı kapat
                await asyncio.to_thread(service.disconnect)
                
            except Exception as e:
                db.rollback()
                logger.error(f"[-] Error syncing account {acc_data['email']}: {str(e)}", exc_info=True)
                continue