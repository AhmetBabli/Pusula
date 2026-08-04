"""
✅ Environment Validation for Production Readiness
"""
import logging
from typing import List, Tuple
from backend.config import settings

logger = logging.getLogger("KariyerAjani.EnvValidation")


def check_required_env_vars() -> List[Tuple[str, bool, str]]:
    """
    Check if all required environment variables are set.
    Returns: List of (var_name, is_valid, message)
    """
    checks = []
    
    # Critical for any environment
    checks.append(
        ("SECRET_KEY", bool(settings.SECRET_KEY and len(settings.SECRET_KEY) > 16),
         "SECRET_KEY must be set and at least 16 characters (use secrets.token_hex(32))")
    )
    
    checks.append(
        ("ENCRYPTION_KEY", bool(settings.ENCRYPTION_KEY),
         "ENCRYPTION_KEY must be set (use Fernet.generate_key())")
    )
    
    # Critical for production
    if not settings.DEBUG:
        checks.append(
            ("GEMINI_API_KEY", bool(settings.GEMINI_API_KEY),
             "GEMINI_API_KEY required in production")
        )
        
        checks.append(
            ("DATABASE_URL", settings.DATABASE_TYPE == "postgresql",
             "PostgreSQL database required in production (not SQLite)")
        )
    
    return checks


def validate_production_readiness() -> Tuple[bool, List[str]]:
    """
    Validate that all production requirements are met.
    Returns: (is_ready, issues)
    """
    if settings.DEBUG:
        return True, []
    
    issues = []
    checks = check_required_env_vars()
    
    for var_name, is_valid, message in checks:
        if not is_valid:
            issues.append(f"❌ {var_name}: {message}")
    
    return len(issues) == 0, issues


def log_env_status():
    """Log environment status on startup."""
    logger.info("=" * 60)
    logger.info(f"🎯 Kariyer Ajanı v{settings.APP_VERSION}")
    logger.info(f"Environment: {'DEVELOPMENT' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"Database: {settings.DATABASE_TYPE.upper()}")
    logger.info(f"CORS Origins: {settings.ALLOWED_ORIGINS}")
    logger.info("=" * 60)
    
    # Check production readiness
    is_ready, issues = validate_production_readiness()
    
    if not is_ready:
        for issue in issues:
            logger.error(issue)
        if not settings.DEBUG:
            raise RuntimeError(f"Production environment not ready. Issues: {len(issues)}")
    else:
        logger.info("✅ All environment checks passed")
