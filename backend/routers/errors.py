"""
🛠️ Error Logging Router for Frontend Errors
"""
import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/errors", tags=["Error Logging"])
logger = logging.getLogger("KariyerAjani.Errors")


class FrontendErrorLog(BaseModel):
    message: str
    stack: Optional[str] = None
    componentStack: Optional[str] = None
    timestamp: str
    userAgent: str
    url: str


@router.post("/log")
async def log_frontend_error(error_data: FrontendErrorLog):
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
