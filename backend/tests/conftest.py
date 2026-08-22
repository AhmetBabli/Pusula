"""
Backend test suite fixtures.

Gerçek dev veritabanına (kariyer_ajani.db) veya gerçek dış servislere
(Gemini, Google OAuth, DuckDuckGo, Gmail) hiçbir testin dokunmaması için:
- `client` fixture'ı get_db'yi bellek-içi (in-memory) izole bir SQLite'a yönlendirir.
- TestClient `with` bloğu olmadan kullanılır, böylece uygulamanın gerçek
  lifespan'i (scheduler başlatma, gerçek init_db) hiç tetiklenmez.
- Rate limiter durumu her testten önce sıfırlanır, testler birbirini etkilemesin.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.rate_limiter import limiter


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # database.py'deki gerçek engine'de olduğu gibi — SQLite'ta foreign key
    # zorlaması varsayılan olarak kapalı, bu pragma açılmadan modellerdeki
    # ondelete="CASCADE"/"SET NULL" testlerde sessizce hiçbir şey yapmaz.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    from backend.models import user, cv, job, job_user_state, event as event_model, event_user_state, application, inbox, outreach  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Her test temiz bir rate-limit sayacıyla başlasın — bir testte tetiklenen
    429, sonraki alakasız bir testi yanlışlıkla etkilemesin."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture()
def client(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def register_and_login(client: TestClient, email: str = "test@example.com", password: str = "sifre1234", full_name: str = "Test Kullanıcı") -> str:
    """Yardımcı: yeni kullanıcı kaydeder, JWT token'ını döner."""
    res = client.post("/api/auth/register", json={"email": email, "password": password, "full_name": full_name})
    assert res.status_code == 201, res.text
    return res.json()["access_token"]
