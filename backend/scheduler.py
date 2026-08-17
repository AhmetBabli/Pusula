import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from backend.config import settings
from backend.database import SessionLocal
from backend.routers.jobs import run_job_sync
from backend.routers.inbox import run_sync_background
from backend.models.inbox import EmailAccount
from backend.models.user import UserProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_async_in_new_loop(coro):
    """
    BackgroundScheduler (sync thread) içinden async fonksiyon çağırmanın
    güvenli yolu: Uvicorn'un event loop'una dokunmadan yeni izole bir loop açar.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def sync_jobs_task():
    """
    run_job_sync() kendi SessionLocal'ını kendi açıyor — dışarıdan db gönderilmez.
    asyncio.new_event_loop() ile Uvicorn loop'una müdahale edilmez.
    """
    logger.info("[Scheduler] İş ilanı senkronizasyonu başlıyor...")
    try:
        _run_async_in_new_loop(run_job_sync())
    except Exception as e:
        logger.error(f"[Scheduler] CRITICAL - İş ilanı senkronizasyonunda hata: {e}")


def sync_inbox_task():
    """
    EmailAccount verilerini önce sync DB session ile çeker,
    sonra async run_sync_background'u yeni loop'ta çalıştırır.

    Not: Hesaplar sahibi kullanıcıya göre gruplanıyor ve her grup KENDİ
    kullanıcısının Gemini key'i ile senkronize ediliyor — tek bir paylaşılan
    key yerine, çok kullanıcılı bir gelecekte herkes kendi kotasını kullansın.
    """
    logger.info("[Scheduler] Gelen kutusu senkronizasyonu başlıyor...")
    try:
        with SessionLocal() as db:
            accounts = db.query(EmailAccount).filter(EmailAccount.is_active == True).all()
            by_user: dict[int, list[dict]] = {}
            api_keys: dict[int, str] = {}
            for acc in accounts:
                by_user.setdefault(acc.user_id, []).append({
                    "id": acc.id,
                    "email": acc.email,
                    "app_password": acc.app_password,
                    "auth_method": acc.auth_method,
                    "oauth_refresh_token": acc.oauth_refresh_token,
                })
                if acc.user_id not in api_keys:
                    owner = db.query(UserProfile).filter(UserProfile.id == acc.user_id).first()
                    api_keys[acc.user_id] = owner.gemini_api_key if owner else ""

        for user_id, accounts_data in by_user.items():
            _run_async_in_new_loop(run_sync_background(accounts_data, api_keys.get(user_id, "")))
    except Exception as e:
        logger.error(f"[Scheduler] CRITICAL - Inbox senkronizasyonunda hata: {e}")


def start_scheduler():
    scheduler.add_job(
        sync_jobs_task, 'interval', hours=settings.SCRAPE_INTERVAL_HOURS, id='job_sync', replace_existing=True
    )
    scheduler.add_job(
        sync_inbox_task, 'interval', minutes=settings.INBOX_SYNC_INTERVAL_MINUTES, id='inbox_sync', replace_existing=True
    )
    scheduler.start()
    logger.info(
        f"[OK] Scheduler başlatıldı (Jobs: {settings.SCRAPE_INTERVAL_HOURS}h, "
        f"Inbox: {settings.INBOX_SYNC_INTERVAL_MINUTES}m)"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[OK] Scheduler güvenle durduruldu.")