"""
🚦 Rate Limiting Configuration for API Protection
"""
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("KariyerAjani.RateLimit")

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour", "20/minute"],  # Global defaults
)


async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom error handler for rate limit exceeded."""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={"detail": "Çok fazla istek yapıldı. Lütfen daha sonra tekrar deneyin."},
    )
