from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from backend.database import get_db
from backend.models.job import Job
from backend.models.job_user_state import JobUserState
from backend.models.event import Event
from backend.models.application import Application
from backend.models.cv import CV
from backend.models.user import UserProfile
from backend.schemas.responses import DashboardStatsOut, JobMatchOut
from backend.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsOut)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Ana panel istatistikleri. İlan/etkinlik sayıları paylaşılan; başvuru/CV/
    ilan-durumu/eşleşme skoru sayıları kullanıcıya özeldir (JobUserState)."""

    # 1. Job İstatistikleri: toplam paylaşılan katalog, "yeni" ise bu kullanıcı
    # için henüz bir JobUserState'i olmayan (veya status="new" olan) ilanlar.
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    new_jobs = (
        db.query(func.count(Job.id))
        .outerjoin(JobUserState, (JobUserState.job_id == Job.id) & (JobUserState.user_id == current_user.id))
        .filter(func.coalesce(JobUserState.status, "new") == "new")
        .scalar() or 0
    )

    # 2. Application İstatistikleri (Kullanıcıya özel)
    app_stats = db.query(
        func.count(Application.id).label("total"),
        func.sum(case((Application.status == "awaiting_approval", 1), else_=0)).label("pending")
    ).filter(Application.user_id == current_user.id).first()

    total_applications = app_stats.total or 0
    pending_approvals = app_stats.pending or 0

    # 3. Diğer Sayımlar: Events paylaşılan, CV kullanıcıya özel
    total_events = db.query(func.count(Event.id)).scalar() or 0
    total_cvs = db.query(func.count(CV.id)).filter(CV.user_id == current_user.id).scalar() or 0

    # 4. En iyi eşleşen 5 ilan (bu kullanıcı için gerçekten eşleştirilmiş olanlar)
    top_match_rows = (
        db.query(Job, JobUserState)
        .join(JobUserState, (JobUserState.job_id == Job.id) & (JobUserState.user_id == current_user.id))
        .order_by(JobUserState.match_score.desc())
        .limit(5)
        .all()
    )
    top_matches = [
        JobMatchOut(
            id=job.id,
            title=job.title,
            company=job.company,
            match_score=round(state.match_score or 0),
            status=state.status,
            created_at=job.scraped_at,
        )
        for job, state in top_match_rows
    ]

    return DashboardStatsOut(
        total_jobs=total_jobs,
        new_jobs=new_jobs,
        total_events=total_events,
        total_applications=total_applications,
        pending_approvals=pending_approvals,
        total_cvs=total_cvs,
        top_matches=top_matches,
    )