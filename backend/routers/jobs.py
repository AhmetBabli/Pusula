import uuid
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db, SessionLocal
from backend.models.job import Job
from backend.models.job_user_state import JobUserState
from backend.models.cv import CV
from backend.models.user import UserProfile
from backend.utils.db_helpers import get_or_404, get_or_create_job_state
from backend.ai.gemini_client import match_job_to_cv, match_jobs_batch
from backend.schemas.agent_contracts import ScrapedJobContract
from backend.routers.tasks import update_task
from backend.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["İş İlanları"])
logger = logging.getLogger(__name__)

# PATCH istekleri için küçük bir Pydantic modeli
class JobStatusUpdate(BaseModel):
    status: str

@router.get("/")
def list_jobs(
    source: str = Query(None, description="Filtre: kariyer_net, linkedin, youthall"),
    status: str = Query(None, description="Filtre: new, reviewed, applied"),
    min_score: float = Query(None, description="Minimum match skoru"),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """İlanları listele (filtreleme ile). İlanlar tüm kullanıcılar arasında
    paylaşılan bir katalogdur; durum/favori/skor ise bu kullanıcıya özel
    (JobUserState) — LEFT JOIN ile, hiç etkileşilmemiş ilanlar varsayılan
    değerlerle (status="new", match_score=0) döner."""
    state_status = func.coalesce(JobUserState.status, "new")
    state_score = func.coalesce(JobUserState.match_score, 0)

    q = (
        db.query(Job, JobUserState)
        .outerjoin(
            JobUserState,
            (JobUserState.job_id == Job.id) & (JobUserState.user_id == current_user.id),
        )
    )

    if source:
        q = q.filter(Job.source == source)
    if status:
        q = q.filter(state_status == status)
    if min_score is not None:
        q = q.filter(state_score >= min_score)

    rows = q.order_by(state_score.desc()).limit(100).all()

    return [
        {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "source": j.source,
            "match_score": state.match_score if state else 0,
            "status": state.status if state else "new",
            "job_type": j.job_type,
            "deadline": j.deadline.isoformat() if j.deadline else None,
            "source_url": j.source_url,
            "is_favorite": state.is_favorite if state else False,
        }
        for j, state in rows
    ]

@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """İlan detayı."""
    job = get_or_404(db, Job, job_id, "İlan")
    state = db.query(JobUserState).filter(
        JobUserState.user_id == current_user.id, JobUserState.job_id == job_id
    ).first()
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "source": job.source,
        "source_url": job.source_url,
        "description": job.description,
        "requirements": job.requirements,
        "match_score": state.match_score if state else 0,
        "match_explanation": state.match_explanation if state else None,
        "best_cv_id": state.best_cv_id if state else None,
        "missing_skills": state.missing_skills if state else [],
        "status": state.status if state else "new",
        "is_favorite": state.is_favorite if state else False,
        "deadline": job.deadline.isoformat() if job.deadline else None,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
    }

@router.patch("/{job_id}/status")
def update_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """İlan durumunu JSON body üzerinden günceller — sadece bu kullanıcı için."""
    get_or_404(db, Job, job_id, "İlan")
    state = get_or_create_job_state(db, current_user.id, job_id)
    state.status = payload.status
    db.commit()
    return {"message": f"İlan durumu '{payload.status}' olarak güncellendi"}

@router.patch("/{job_id}/favorite")
def toggle_favorite(job_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Favorilere ekle/çıkar — sadece bu kullanıcı için."""
    get_or_404(db, Job, job_id, "İlan")
    state = get_or_create_job_state(db, current_user.id, job_id)
    state.is_favorite = not state.is_favorite
    db.commit()
    return {"is_favorite": state.is_favorite}

@router.post("/{job_id}/match")
async def match_job(
    job_id: int,
    cv_id: int = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """İlanı CV ile eşleştir ve skor hesapla — sadece bu kullanıcı için."""
    job = get_or_404(db, Job, job_id, "İlan")

    cv_query = db.query(CV).filter(CV.user_id == current_user.id)
    if cv_id:
        cv = cv_query.filter(CV.id == cv_id).first()
    else:
        cv = cv_query.filter(CV.is_default == True).first()

    if not cv or not cv.extracted_text:
        raise HTTPException(status_code=400, detail="Eşleştirilecek CV bulunamadı")

    result = await match_job_to_cv(job.description or "", cv.extracted_text, current_user.skills or [], api_key=current_user.gemini_api_key)

    state = get_or_create_job_state(db, current_user.id, job_id)
    state.match_score = result.get("score", 0)
    state.match_explanation = result.get("explanation", "")
    state.missing_skills = result.get("missing_skills", [])
    state.best_cv_id = cv.id
    state.status = "reviewed"
    db.commit()

    return {"job_id": job.id, "match": result}


# ─── SYNC ENDPOINT — SSE Task Tracker ile ───
@router.post("/sync", status_code=202)
async def sync_jobs(background_tasks: BackgroundTasks, current_user: UserProfile = Depends(get_current_user)):
    """
    Senkronizasyonu arka plana atar ve takip edilebilir bir task_id döner.
    Frontend: GET /api/tasks/{task_id}/stream ile SSE üzerinden durumu izler.
    """
    task_id = str(uuid.uuid4())
    update_task(task_id, "pending", 0)
    background_tasks.add_task(_run_job_sync_tracked, task_id)
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Senkronizasyon başlatıldı. /api/tasks/{task_id}/stream adresinden takip edin.",
    }


async def _run_job_sync_tracked(task_id: str):
    """run_job_sync()'u task tracker ile sarar — hata/başarı SSE'ye yansır."""
    update_task(task_id, "running", 10)
    try:
        await run_job_sync()
        update_task(task_id, "done", 100, result={"message": "Senkronizasyon tamamlandı."})
    except Exception as e:
        logger.error(f"[sync_tracked] Hata: {e}")
        update_task(task_id, "failed", 0, error=str(e))


# Tek Gemini isteğinde eşleştirilecek ilan sayısı. Önceden her ilan ayrı bir
# istekti (154 ilan = 154 istek); artık gruplar halinde tek istekte gidiyor —
# günlük kotayı ~BATCH_SIZE kat daha az tüketiyor.
MATCH_BATCH_SIZE = 8


# ─── ARKA PLAN GÖREVİ (Kendi DB Session'ını Kendi Yönetir) ───
async def run_job_sync():
    """Arka plan görevi: Çoklu Platform Scrape + (her kullanıcı için ayrı ayrı)
    Toplu (batch) AI Match. Job satırı paylaşılan bir katalog, ama eşleştirme
    kullanıcıya özel (JobUserState) — bu yüzden burada TEK bir "global"
    CV yerine, CV'si olan HER kullanıcı için ayrı bir eşleştirme turu
    çalıştırılır."""
    import random
    from backend.scrapers.youthall_scraper import YouthallScraper
    from backend.scrapers.kariyer_net_scraper import KariyerNetScraper
    from backend.scrapers.linkedin_scraper import LinkedInScraper
    from backend.scrapers.arbeitnow_scraper import ArbeitnowScraper

    scrapers = [YouthallScraper(), KariyerNetScraper(), LinkedInScraper(), ArbeitnowScraper()]
    new_jobs_data = []

    # API'den bağımsız olduğu için kendi SessionLocal'ımızı açıyoruz!
    with SessionLocal() as db:
        user = db.query(UserProfile).first()

        # Dinamik arama terimi belirleme (herhangi bir kullanıcının hedef
        # sektöründen — tarama tüm kullanıcılar için ortak bir katalog besliyor)
        target_sectors = user.target_sectors if user and user.target_sectors else ["Yazılım", "IT", "Teknoloji"]
        search_keyword = random.choice(target_sectors)
        query = f"{search_keyword}"

        logger.info(f"[SYNC] İş ilanları kazınmaya başlıyor. Seçilen hedef: {query}")

        for s in scrapers:
            try:
                # Scraper'ların bazıları async bazıları sync
                if isinstance(s, YouthallScraper):
                    platform_jobs = await asyncio.to_thread(s.scrape_jobs, limit=15, query=query)
                elif isinstance(s, KariyerNetScraper):
                    platform_jobs = await s.scrape_jobs(query=query, limit=15)
                elif isinstance(s, LinkedInScraper): # LinkedIn (sync)
                    platform_jobs = await asyncio.to_thread(s.scrape_jobs, query=query, limit=15)
                else: # ArbeitnowScraper (sync, no query parameter)
                    platform_jobs = await asyncio.to_thread(s.scrape_jobs, limit=15)

                if platform_jobs:
                    new_jobs_data.extend(platform_jobs)
            except Exception as e:
                logger.error(f"[-] Scraper error ({s.__class__.__name__}): {e}")

        added_count = 0
        skipped_count = 0

        for raw_job_data in new_jobs_data:
            # ── 1. Şema doğrulaması: Kontrat geçmezse bu ilanı atla ──
            try:
                validated = ScrapedJobContract.model_validate(raw_job_data)
                job_dict = validated.to_job_dict()
            except Exception as validation_err:
                logger.warning(f"[SCHEMA] İlan kontrat doğrulamasından geçemedi, atlandı: {validation_err}")
                skipped_count += 1
                continue

            # ── 2. Duplicate kontrolü ──
            existing = db.query(Job).filter(Job.source_url == job_dict["source_url"]).first()
            if existing:
                continue

            # ── 3. Job oluştur ──
            new_job = Job(**job_dict)
            db.add(new_job)
            added_count += 1

        db.flush()

        # ── 4. Her kullanıcı için ayrı ayrı toplu (batch) AI eşleştirme ──
        # CV'si olan her kullanıcı, henüz KENDİ güncel varsayılan CV'sine göre
        # eşleşmemiş (hiç JobUserState'i olmayan veya eski bir CV'ye göre
        # puanlanmış) tüm ilanlar için MATCH_BATCH_SIZE'lık gruplar halinde
        # eşleştirilir — böylece bir kullanıcı CV'sini sisteme yeni yüklese
        # bile, ondan önce taranmış ilanlar da kalıcı olarak %0 görünmüyor.
        users_with_cv = (
            db.query(UserProfile, CV)
            .join(CV, (CV.user_id == UserProfile.id) & (CV.is_default == True))
            .filter(CV.extracted_text.isnot(None))
            .all()
        )

        total_matched = 0
        for match_user, default_cv in users_with_cv:
            skills = match_user.skills or []
            match_api_key = match_user.gemini_api_key

            existing_state_job_ids = {
                s.job_id
                for s in db.query(JobUserState.job_id).filter(
                    JobUserState.user_id == match_user.id, JobUserState.best_cv_id == default_cv.id
                ).all()
            }
            pending_jobs = db.query(Job).filter(~Job.id.in_(existing_state_job_ids)).all() if existing_state_job_ids else db.query(Job).all()
            pending_match = [
                (job, " ".join(part for part in [job.description, job.requirements, job.title] if part))
                for job in pending_jobs
            ]
            if not pending_match:
                continue

            for i in range(0, len(pending_match), MATCH_BATCH_SIZE):
                chunk = pending_match[i:i + MATCH_BATCH_SIZE]
                jobs_payload = [{"id": job.id, "description": desc} for job, desc in chunk]
                try:
                    batch_results = await match_jobs_batch(jobs_payload, default_cv.extracted_text, skills, api_key=match_api_key)
                except Exception as e:
                    logger.error(f"[-] Batch match hatası (kullanıcı {match_user.id}, grup {i // MATCH_BATCH_SIZE}): {e}")
                    batch_results = {}

                for job, _desc in chunk:
                    result = batch_results.get(job.id)
                    if not result:
                        # Model bu ilanı atladıysa bir sonraki sync'te tekrar denenir.
                        continue
                    state = get_or_create_job_state(db, match_user.id, job.id)
                    state.match_score = result.get("score", 0)
                    state.match_explanation = result.get("explanation", "")
                    state.missing_skills = result.get("missing_skills", [])
                    if result.get("ai_powered"):
                        state.best_cv_id = default_cv.id
                        if state.status == "new":
                            state.status = "reviewed"
                        total_matched += 1

        db.commit()
        logger.info(
            f"[OK] Sync complete. Added: {added_count}, Skipped (schema): {skipped_count}, "
            f"Matched (AI, batch, {len(users_with_cv)} kullanıcı): {total_matched}, Query: '{query}'."
        )

