import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from backend.database import SessionLocal
from backend.routers.jobs import run_job_sync
from backend.routers.inbox import run_sync_background
from backend.models.inbox import EmailAccount

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
    """
    logger.info("[Scheduler] Gelen kutusu senkronizasyonu başlıyor...")
    try:
        with SessionLocal() as db:
            accounts = db.query(EmailAccount).filter(EmailAccount.is_active == True).all()
            accounts_data = [
                {"id": acc.id, "email": acc.email, "app_password": acc.app_password}
                for acc in accounts
            ]
        if accounts_data:
            _run_async_in_new_loop(run_sync_background(accounts_data))
    except Exception as e:
        logger.error(f"[Scheduler] CRITICAL - Inbox senkronizasyonunda hata: {e}")


def start_scheduler():
    scheduler.add_job(sync_jobs_task, 'interval', hours=2, id='job_sync', replace_existing=True)
    scheduler.add_job(sync_inbox_task, 'interval', minutes=30, id='inbox_sync', replace_existing=True)
    scheduler.start()
    logger.info("[OK] Scheduler başlatıldı (Jobs: 2h, Inbox: 30m)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[OK] Scheduler güvenle durduruldu.")