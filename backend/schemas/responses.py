from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime, timezone

class JobMatchOut(BaseModel):
    id: int
    title: str
    company: str
    match_score: int
    status: str
    created_at: datetime

    # JobUserState.status/created_at nullable DB sütunları — bir migration
    # backfill'inde (ör. eski Job.status/is_favorite'ın JobUserState'e
    # taşınması) satır elle/kısmi doldurulmuşsa NULL kalabilir. Tek bir NULL
    # satır, work_experiences/certificates'te yaşandığı gibi, bu ucu kalıcı
    # olarak 500'e düşürmesin diye burada da aynı savunma uygulanıyor.
    @field_validator("status", mode="before")
    @classmethod
    def _none_to_new(cls, v):
        return v if v is not None else "new"

    @field_validator("created_at", mode="before")
    @classmethod
    def _none_to_now(cls, v):
        return v if v is not None else datetime.now(timezone.utc)

    model_config = ConfigDict(from_attributes=True)

class CVVariantPerformanceOut(BaseModel):
    variant_type: str
    cv_count: int
    application_count: int
    matched_job_count: int
    avg_match_score: float
    interview_count: int = 0
    offer_count: int = 0

class DashboardStatsOut(BaseModel):
    total_jobs: int
    new_jobs: int
    total_events: int
    total_applications: int
    pending_approvals: int
    total_cvs: int
    top_matches: List[JobMatchOut]
    cv_variant_performance: List[CVVariantPerformanceOut] = []

    model_config = ConfigDict(from_attributes=True)
