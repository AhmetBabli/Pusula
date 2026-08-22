"""
🛠️ Error Logging Router for Frontend Errors
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator

from backend.rate_limiter import limiter

router = APIRouter(prefix="/api/errors", tags=["Error Logging"])
logger = logging.getLogger("KariyerAjani.Errors")

# Girişsiz bir uç sınırsız uzunlukta metin kabul edip doğrudan log dosyalarına
# yazıyordu — basit bir döngü diski doldurup uygulamayı durdurabilirdi.
_MAX_FIELD_LENGTH = 2000


class FrontendErrorLog(BaseModel):
    message: str
    stack: Optional[str] = None
    componentStack: Optional[str] = None
    timestamp: str
    userAgent: str
    url: str

    @field_validator("message", "stack", "componentStack", mode="before")
    @classmethod
    def _truncate(cls, v):
        return v[:_MAX_FIELD_LENGTH] if isinstance(v, str) else v


@router.post("/log")
@limiter.limit("30/hour")
async def log_frontend_error(request: Request, error_data: FrontendErrorLog):
    """Log frontend errors to backend"""
    logger.error(
        f"FRONTEND ERROR | URL: {error_data.url} | MSG: {error_data.message}",
        extra={
            "component_stack": error_data.componentStack,
            "stack": error_data.stack,
            "timestamp": error_data.timestamp,
            "user_agent": error_data.userAgent,
        }
    )
    return {"status": "logged"}
