from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from backend.database import get_db
from backend.models.job import Job
from backend.models.event import Event
from backend.models.application import Application
from backend.models.cv import CV
from backend.models.user import UserProfile
from backend.schemas.responses import DashboardStatsOut, JobMatchOut
from backend.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsOut)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Ana panel istatistikleri. İlan/etkinlik sayıları paylaşılan; başvuru/CV sayıları kullanıcıya özeldir."""

    # 1. Job İstatistikleri (Paylaşılan/global katalog — tüm kullanıcılar için ortak)
    # case() kullanarak veritabanına tek seferde "Hem hepsini say, hem de 'new' olanları topla" diyoruz.
    job_stats = db.query(
        func.count(Job.id).label("total"),
        func.sum(case((Job.status == "new", 1), else_=0)).label("new_jobs")
    ).first()

    total_jobs = job_stats.total or 0
    new_jobs = job_stats.new_jobs or 0

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

    # 4. En iyi eşleşen 5 ilan
    top_matches = db.query(Job).order_by(Job.match_score.desc()).limit(5).all()

    # NOT: Pydantic şemalarında (DashboardStatsOut ve JobMatchOut) Config içinde 
    # `from_attributes = True` ayarlı olduğu sürece veriyi manuel dönüştürmeye gerek yoktur.
    return DashboardStatsOut(
        total_jobs=total_jobs,
        new_jobs=new_jobs,
        total_events=total_events,
        total_applications=total_applications,
        pending_approvals=pending_approvals,
        total_cvs=total_cvs,
        top_matches=top_matches,  # SQLAlchemy listesini doğrudan verdik, Pydantic halledecek!
    )