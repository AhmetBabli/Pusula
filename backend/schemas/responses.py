from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class JobMatchOut(BaseModel):
    id: int
    title: str
    company: str
    match_score: int
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DashboardStatsOut(BaseModel):
    total_jobs: int
    new_jobs: int
    total_events: int
    total_applications: int
    pending_approvals: int
    total_cvs: int
    top_matches: List[JobMatchOut]

    model_config = ConfigDict(from_attributes=True)
