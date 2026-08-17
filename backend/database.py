"""
Kariyer Ajanı — Database Setup (SQLAlchemy + SQLite/PostgreSQL)
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

logger = logging.getLogger("KariyerAjani.Database")

# Database engine configuration
engine_config = {
    "echo": settings.DEBUG,
}

# Add connection args based on database type
if settings.DATABASE_TYPE == "sqlite":
    engine_config["connect_args"] = {"check_same_thread": False}
    logger.warning("⚠️ Using SQLite - suitable only for development. Use PostgreSQL for production.")
elif settings.DATABASE_TYPE == "postgresql":
    engine_config["pool_size"] = 10
    engine_config["max_overflow"] = 20
    engine_config["pool_pre_ping"] = True  # Test connection before using
    logger.info("PostgreSQL database configured")

engine = create_engine(settings.DATABASE_URL, **engine_config)

# SQLite'ta foreign key zorlaması VARSAYILAN OLARAK KAPALIDIR — modellerdeki
# ondelete="CASCADE"/"SET NULL" tanımları bu PRAGMA açılmadan sessizce hiçbir
# şey yapmaz (silinen bir CV/iş ilanı/e-posta hesabı, bağlı Application/InboxItem
# satırlarını "sahipsiz" bırakır). Her yeni bağlantıda açıkça etkinleştiriyoruz.
if settings.DATABASE_TYPE == "sqlite":
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def get_db():
    """FastAPI dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once at startup."""
    from backend.models import user, cv, job, event, application, inbox, outreach  # noqa: F401
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully ({settings.DATABASE_TYPE})")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
