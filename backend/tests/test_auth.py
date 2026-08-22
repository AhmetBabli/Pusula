"""
Kimlik doğrulama testleri: kayıt, giriş ve rate limiting.

Bu dosyadaki testler bu oturumda düzeltilen gerçek bug'ları regresyona karşı
kilitliyor:
- test_register_does_not_leak_fake_defaults: SQLAlchemy'nin `university=None`
  atamasını modelin sahte default'uyla ("Doğuş Üniversitesi") sessizce
  değiştirmesi bug'ı.
- test_login_is_rate_limited_after_five_attempts: /auth/login'in daha önce
  hiç sınırlanmıyor olması bug'ı.
- test_logout_invalidates_previous_token: audit item #11 — JWT'lerin sunucu
  taraflı iptal mekanizması yoktu, /logout bir no-op'tan ibaretti.
- test_google_login_does_not_hijack_other_users_email_account: audit item
  #11 — Google girişi, başka bir kullanıcının app-password ile bağladığı
  Gmail hesabını sessizce çalabiliyordu.
"""
from backend.tests.conftest import register_and_login


def test_register_creates_user_and_returns_token(client):
    res = client.post("/api/auth/register", json={
        "email": "yeni@example.com",
        "password": "guclusifre123",
        "full_name": "Yeni Kullanıcı",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["access_token"]
    assert body["user"]["email"] == "yeni@example.com"


def test_register_does_not_leak_fake_defaults(client):
    """Regresyon testi: university/department None olarak kalmalı, modelin
    eski sahte varsayılanlarıyla ("Doğuş Üniversitesi" vb.) doldurulmamalı."""
    token = register_and_login(client, email="fakedefault@example.com")

    res = client.get("/api/users/profile", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    profile = res.json()
    assert profile["university"] is None
    assert profile["department"] is None
    assert profile["skills"] == []
    assert profile["target_sectors"] == []
    assert profile["onboarding_completed"] is False


def test_register_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": "sifre1234", "full_name": "A"})
    res = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "sifre1234", "full_name": "B"})
    assert res.status_code == 400


def test_register_short_password_rejected(client):
    res = client.post("/api/auth/register", json={"email": "kisasifre@example.com", "password": "1234", "full_name": "A"})
    assert res.status_code == 400


def test_login_success(client):
    client.post("/api/auth/register", json={"email": "giris@example.com", "password": "sifre1234", "full_name": "A"})
    res = client.post("/api/auth/login", json={"email": "giris@example.com", "password": "sifre1234"})
    assert res.status_code == 200
    assert res.json()["access_token"]


def test_login_wrong_password_rejected(client):
    client.post("/api/auth/register", json={"email": "yanlis@example.com", "password": "sifre1234", "full_name": "A"})
    res = client.post("/api/auth/login", json={"email": "yanlis@example.com", "password": "yanlissifre"})
    assert res.status_code == 401


def test_login_nonexistent_email_rejected(client):
    res = client.post("/api/auth/login", json={"email": "yok@example.com", "password": "sifre1234"})
    assert res.status_code == 401


def test_login_is_rate_limited_after_five_attempts(client):
    """Regresyon testi: rate limiter middleware olmadan @limiter.limit(...)
    dekoratörleri hiçbir işe yaramıyordu; /auth/login sınırsız deneme kabul
    ediyordu. Artık 5/dakika sonrası 429 dönmeli."""
    payload = {"email": "bruteforce@example.com", "password": "yanlissifre"}

    for _ in range(5):
        res = client.post("/api/auth/login", json=payload)
        assert res.status_code == 401

    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 429


def test_logout_invalidates_previous_token(client):
    """Regresyon testi: /logout artık sadece istemcinin token'ı silmesine
    güvenmiyor — token_version'ı artırıp o ana kadar üretilmiş tüm JWT'leri
    sunucu tarafında geçersiz kılıyor."""
    token = register_and_login(client, email="logout@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/users/profile", headers=headers)
    assert res.status_code == 200

    res = client.post("/api/auth/logout", headers=headers)
    assert res.status_code == 204

    res = client.get("/api/users/profile", headers=headers)
    assert res.status_code == 401


def test_google_login_does_not_hijack_other_users_email_account(client, db_session, monkeypatch):
    """Regresyon testi: A kullanıcısı b@gmail.com'u app-password ile bağlamışsa,
    biri Google ile b@gmail.com olarak giriş yapınca bu hesap sessizce el
    değiştirmemeli."""
    import backend.routers.auth as auth_module
    from backend.models.user import UserProfile
    from backend.models.inbox import EmailAccount

    monkeypatch.setattr(auth_module.settings, "GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setattr(auth_module.settings, "GOOGLE_CLIENT_SECRET", "fake-client-secret")

    register_and_login(client, email="owner@example.com")
    owner = db_session.query(UserProfile).filter(UserProfile.email == "owner@example.com").first()
    db_session.add(EmailAccount(user_id=owner.id, email="b@gmail.com"))
    db_session.commit()

    class _FakeResponse:
        def __init__(self, json_data):
            self.ok = True
            self.status_code = 200
            self._json = json_data

        def json(self):
            return self._json

    def fake_post(url, data=None, timeout=None):
        return _FakeResponse({
            "access_token": "fake-google-access-token",
            "refresh_token": "fake-refresh-token",
            "scope": "https://www.googleapis.com/auth/gmail.send",
        })

    def fake_get(url, headers=None, timeout=None):
        return _FakeResponse({"email": "b@gmail.com", "email_verified": True, "name": "Google Kullanıcı"})

    monkeypatch.setattr(auth_module.requests, "post", fake_post)
    monkeypatch.setattr(auth_module.requests, "get", fake_get)

    res = client.post("/api/auth/google", json={"code": "fake-auth-code"})
    assert res.status_code == 200

    db_session.expire_all()
    linked = db_session.query(EmailAccount).filter(EmailAccount.email == "b@gmail.com").one()
    assert linked.user_id == owner.id
