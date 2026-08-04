import uuid
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db, SessionLocal
from backend.models.job import Job
from backend.models.cv import CV
from backend.models.user import UserProfile
from backend.utils.db_helpers import get_or_404
from backend.ai.gemini_client import match_job_to_cv
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
    """İlanları listele (filtreleme ile). İlanlar tüm kullanıcılar arasında paylaşılan bir katalogdur."""
    q = db.query(Job).order_by(Job.match_score.desc())

    if source:
        q = q.filter(Job.source == source)
    if status:
        q = q.filter(Job.status == status)
    if min_score is not None:
        q = q.filter(Job.match_score >= min_score)

    jobs = q.limit(100).all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "source": j.source,
            "match_score": j.match_score,
            "status": j.status,
            "job_type": j.job_type,
            "deadline": j.deadline.isoformat() if j.deadline else None,
            "source_url": j.source_url,
            "is_favorite": j.is_favorite,
        }
        for j in jobs
    ]

@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """İlan detayı."""
    job = get_or_404(db, Job, job_id, "İlan")
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "source": job.source,
        "source_url": job.source_url,
        "description": job.description,
        "requirements": job.requirements,
        "match_score": job.match_score,
        "match_explanation": job.match_explanation,
        "best_cv_id": job.best_cv_id,
        "missing_skills": job.missing_skills,
        "status": job.status,
        "is_favorite": job.is_favorite,
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
    """İlan durumunu JSON body üzerinden güncelle."""
    job = get_or_404(db, Job, job_id, "İlan")
    job.status = payload.status
    db.commit()
    return {"message": f"İlan durumu '{payload.status}' olarak güncellendi"}

@router.patch("/{job_id}/favorite")
def toggle_favorite(job_id: int, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Favorilere ekle/çıkar."""
    job = get_or_404(db, Job, job_id, "İlan")
    job.is_favorite = not job.is_favorite
    db.commit()
    return {"is_favorite": job.is_favorite}

@router.post("/{job_id}/match")
async def match_job(
    job_id: int,
    cv_id: int = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """İlanı CV ile eşleştir ve skor hesapla."""
    job = get_or_404(db, Job, job_id, "İlan")

    cv_query = db.query(CV).filter(CV.user_id == current_user.id)
    if cv_id:
        cv = cv_query.filter(CV.id == cv_id).first()
    else:
        cv = cv_query.filter(CV.is_default == True).first()

    if not cv or not cv.extracted_text:
        raise HTTPException(status_code=400, detail="Eşleştirilecek CV bulunamadı")

    result = await match_job_to_cv(job.description or "", cv.extracted_text, current_user.skills or [])

    job.match_score = result.get("score", 0)
    job.match_explanation = result.get("explanation", "")
    job.missing_skills = json.dumps(result.get("missing_skills", []), ensure_ascii=False)
    job.best_cv_id = cv.id
    job.status = "reviewed"
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


# ─── ARKA PLAN GÖREVİ (Kendi DB Session'ını Kendi Yönetir) ───
async def run_job_sync():
    """Arka plan görevi: Çoklu Platform Scrape + AI Match."""
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
        skills = user.skills if user and user.skills else []
        
        # Dinamik arama terimi belirleme
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

        default_cv = db.query(CV).filter(CV.is_default == True).first()

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
            db.flush()  # Sadece ID almak için
            added_count += 1

            # ── 4. AI Match (CV varsa) ──
            if default_cv and default_cv.extracted_text:
                try:
                    desc = " ".join(
                        part for part in [new_job.description, new_job.requirements, new_job.title] if part
                    )
                    match_result = await match_job_to_cv(desc, default_cv.extracted_text, skills)

                    new_job.match_score = match_result.get("score", 0)
                    new_job.match_explanation = match_result.get("explanation", "")
                    # ✅ DÜZELTME: missing_skills Column(JSON) → Python listesi bekler, json.dumps YANLIŞ
                    new_job.missing_skills = match_result.get("missing_skills", [])
                    new_job.best_cv_id = default_cv.id
                    new_job.status = "reviewed"
                except Exception as e:
                    logger.error(f"[-] Auto-match error for job {new_job.id}: {e}")

        db.commit()
        logger.info(
            f"[OK] Sync complete. Added: {added_count}, Skipped (schema): {skipped_count}, Query: '{query}'."
        )

class N8nWebhookPayload(BaseModel):
    jobs: list[dict]

# ─── N8N WEBHOOK ───
@router.post("/n8n-webhook")
def receive_n8n_jobs(payload: N8nWebhookPayload, db: Session = Depends(get_db)):
    """n8n üzerinden gelen toplu ilan verilerini alır ve veritabanına kaydeder."""
    added = 0
    skipped = 0
    for raw in payload.jobs:
        try:
            validated = ScrapedJobContract.model_validate(raw)
            j_dict = validated.to_job_dict()
            # Duplicate check
            if not db.query(Job).filter(Job.source_url == j_dict["source_url"]).first():
                db.add(Job(**j_dict))
                added += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"n8n webhook data parse hatası: {e}")
            skipped += 1
            
    db.commit()
    return {"status": "success", "added": added, "skipped": skipped}