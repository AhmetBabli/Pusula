"""
🔴 Custom Exception Types for Better Error Handling
"""
import logging
from typing import Optional
from fastapi import HTTPException, status

logger = logging.getLogger("KariyerAjani.Exceptions")


class KariyerAjaniException(Exception):
    """Base exception for Kariyer Ajanı"""
    pass


class AuthenticationError(KariyerAjaniException):
    """Authentication failed"""
    pass


class AuthorizationError(KariyerAjaniException):
    """User lacks permission"""
    pass


class ValidationError(KariyerAjaniException):
    """Input validation failed"""
    pass


class AIServiceError(KariyerAjaniException):
    """AI service (Gemini) call failed"""
    pass


class TimeoutError(KariyerAjaniException):
    """Operation timed out"""
    pass


class DatabaseError(KariyerAjaniException):
    """Database operation failed"""
    pass


class FileOperationError(KariyerAjaniException):
    """File operation failed"""
    pass


class ExternalServiceError(KariyerAjaniException):
    """External service (scraper, email) failed"""
    pass


def exception_to_http_exception(
    exc: Exception,
    status_code: Optional[int] = None,
    headers: Optional[dict] = None
) -> HTTPException:
    """Convert custom exceptions to HTTPException."""
    
    exc_map = {
        AuthenticationError: (status.HTTP_401_UNAUTHORIZED, "Authentication failed"),
        AuthorizationError: (status.HTTP_403_FORBIDDEN, "Access denied"),
        ValidationError: (status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid input"),
        AIServiceError: (status.HTTP_503_SERVICE_UNAVAILABLE, "AI service unavailable"),
        TimeoutError: (status.HTTP_504_GATEWAY_TIMEOUT, "Request timeout"),
        DatabaseError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error"),
        FileOperationError: (status.HTTP_400_BAD_REQUEST, "File operation failed"),
        ExternalServiceError: (status.HTTP_502_BAD_GATEWAY, "External service error"),
    }
    
    exc_type = type(exc)
    if exc_type in exc_map:
        code, detail = exc_map[exc_type]
        status_code = status_code or code
        default_detail = detail
    else:
        status_code = status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
        default_detail = "Internal server error"
    
    detail = str(exc) if str(exc) else default_detail
    
    # Log detailed error
    logger.error(f"Exception: {exc_type.__name__} - {detail}")
    
    return HTTPException(
        status_code=status_code,
        detail=detail if not isinstance(exc, KariyerAjaniException) or str(exc) else detail,
        headers=headers,
    )
