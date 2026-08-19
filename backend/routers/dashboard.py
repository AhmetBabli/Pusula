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
from backend.schemas.responses import DashboardStatsOut, JobMatchOut, CVVariantPerformanceOut
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

    # 5. CV varyant performansı: her varyant tipi için kaç CV var, kaç başvuruda
    # kullanılmış ve (bu kullanıcının JobUserState'lerinde best_cv_id o varyanttan
    # bir CV'ye işaret ediyorsa) ortalama eşleşme skoru ne. (1) numaralı borç
    # düzeltmesiyle match_score artık kullanıcıya özel olduğu için mümkün oldu.
    cv_counts = dict(
        db.query(CV.variant_type, func.count(CV.id))
        .filter(CV.user_id == current_user.id)
        .group_by(CV.variant_type)
        .all()
    )

    app_counts = dict(
        db.query(CV.variant_type, func.count(Application.id))
        .join(Application, Application.cv_id == CV.id)
        .filter(CV.user_id == current_user.id, Application.user_id == current_user.id)
        .group_by(CV.variant_type)
        .all()
    )

    # Gerçek sonuçlar (mülakat/teklif) — eşleşme skoru gibi zayıf bir vekil
    # yerine kullanıcının bizzat işaretlediği asıl veri. "offer" durumundaki
    # bir başvuru zaten bir mülakattan geçmiş demektir, o yüzden ikisini de sayıyoruz.
    interview_counts = dict(
        db.query(CV.variant_type, func.count(Application.id))
        .join(Application, Application.cv_id == CV.id)
        .filter(
            CV.user_id == current_user.id,
            Application.user_id == current_user.id,
            Application.status.in_(("interview", "offer")),
        )
        .group_by(CV.variant_type)
        .all()
    )
    offer_counts = dict(
        db.query(CV.variant_type, func.count(Application.id))
        .join(Application, Application.cv_id == CV.id)
        .filter(
            CV.user_id == current_user.id,
            Application.user_id == current_user.id,
            Application.status == "offer",
        )
        .group_by(CV.variant_type)
        .all()
    )

    match_rows = (
        db.query(CV.variant_type, func.avg(JobUserState.match_score), func.count(JobUserState.id))
        .join(JobUserState, JobUserState.best_cv_id == CV.id)
        .filter(CV.user_id == current_user.id, JobUserState.user_id == current_user.id)
        .group_by(CV.variant_type)
        .all()
    )
    match_map = {variant: (avg_score, matched_count) for variant, avg_score, matched_count in match_rows}

    cv_variant_performance = [
        CVVariantPerformanceOut(
            variant_type=variant,
            cv_count=cv_count,
            application_count=app_counts.get(variant, 0),
            matched_job_count=match_map.get(variant, (0, 0))[1],
            avg_match_score=round(match_map.get(variant, (0, 0))[0] or 0, 1),
            interview_count=interview_counts.get(variant, 0),
            offer_count=offer_counts.get(variant, 0),
        )
        for variant, cv_count in cv_counts.items()
    ]

    return DashboardStatsOut(
        total_jobs=total_jobs,
        new_jobs=new_jobs,
        total_events=total_events,
        total_applications=total_applications,
        pending_approvals=pending_approvals,
        total_cvs=total_cvs,
        top_matches=top_matches,
        cv_variant_performance=cv_variant_performance,
    )