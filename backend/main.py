"""
🎯 Kariyer Ajanı — Ana Uygulama
AI destekli kariyer asistanı: staj/iş ilanları tarıyor,
CV yönetiyor, motivasyon mektubu yazıyor, başvuruları yönetiyor.
"""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# ── Path Ayarı ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.database import init_db
from backend.rate_limiter import limiter, rate_limit_error_handler
from backend.exceptions import KariyerAjaniException, exception_to_http_exception

# Logger setup
from backend.logging_config import setup_logging
setup_logging()
logger = logging.getLogger("KariyerAjani.Main")

# Router imports
from backend.routers import dashboard, cv, jobs, applications, users, events, inbox, outreach, tasks, errors, auth as auth_router
from backend.routers import agents as agents_router
from backend.routers import ws as ws_router

# ── Security Middleware'leri ──
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10 MB

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "İstek boyutu çok büyük. Maksimum 10 MB."},
            )
        return await call_next(request)


# 🚀 YENİ: Modern Lifespan (Yaşam Döngüsü) Yönetimi
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Sistem Başlarken (Startup) ---
    from backend.env_validation import log_env_status
    
    log_env_status()
    init_db()
    from backend.scheduler import start_scheduler, stop_scheduler
    
    try:
        start_scheduler()
    except Exception as e:
        logger.warning(f"[!] Scheduler başlatılamadı: {e}")
        
    logger.info(f"[OK] {settings.APP_NAME} v{settings.APP_VERSION} başlatıldı!")
    logger.info(f"[OK] API dokümantasyonu: http://localhost:8000/docs")
    logger.info(f"[OK] DEBUG modu: {settings.DEBUG}")
    
    yield  # Uygulama burada çalışmaya başlar ve istekleri dinler
    
    # --- Sistem Kapanırken (Shutdown) ---
    logger.info("\n🛑 Kariyer Ajanı kapanıyor, arka plan servisleri temizleniyor...")
    stop_scheduler() # Arka plan görevleri güvenle kapatılıyor


def create_app() -> FastAPI:
    docs_url = "/docs" if settings.DEBUG else None
    redoc_url = "/redoc" if settings.DEBUG else None

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI destekli kariyer asistanı — staj/iş/etkinlik bulucu, CV yöneticisi, başvuru otomasyonu",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan, # Lifespan buraya bağlandı
    )

    # ── Güvenlik Middleware'leri ──
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)

    # CORS — Optimize for production
    cors_config = {
        "allow_origins": settings.ALLOWED_ORIGINS if not settings.DEBUG else ["*"],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "max_age": 3600,  # 1 hour cache
    }
    app.add_middleware(CORSMiddleware, **cors_config)
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)

    # Router'lar
    app.include_router(auth_router.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(cv.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(applications.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(inbox.router, prefix="/api")
    app.include_router(outreach.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(agents_router.router, prefix="/api")
    app.include_router(errors.router)  # Error logging (no prefix)
    app.include_router(ws_router.router)  # WebSocket — prefix yok, /ws/... direkt

    # 🚀 YENİ: Global Exception Handlers (Beklenmeyen çökmeleri şık yakalar)
    @app.exception_handler(KariyerAjaniException)
    async def custom_exception_handler(request: Request, exc: KariyerAjaniException):
        """Handle custom Kariyer Ajanı exceptions."""
        http_exc = exception_to_http_exception(exc)
        return JSONResponse(
            status_code=http_exc.status_code,
            content={"detail": http_exc.detail},
            headers=http_exc.headers,
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error on {request.url}: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "detail": "İstek verisi doğru formatta değil",
                "errors": [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()],
            },
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catch-all handler for unexpected exceptions."""
        logger.error(f"[CRITICAL ERROR] {request.method} {request.url} - {type(exc).__name__}: {exc}")
        
        # Check if it's our custom exception
        if isinstance(exc, KariyerAjaniException):
            http_exc = exception_to_http_exception(exc)
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"detail": http_exc.detail},
            )
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Sunucu tarafında beklenmeyen bir hata oluştu.",
                "error": str(exc) if settings.DEBUG else "Internal server error",
            },
        )

    @app.get("/", tags=["Root"])
    def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs" if settings.DEBUG else "disabled",
            "message": "Kariyer Ajanı API çalışıyor! 🎯",
        }

    @app.get("/health", tags=["Root"])
    def health():
        return {"status": "ok"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )