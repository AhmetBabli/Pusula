"""
Kimlik doğrulama testleri: kayıt, giriş ve rate limiting.

Bu dosyadaki iki test özellikle bu oturumda düzeltilen iki gerçek bug'ı
regresyona karşı kilitliyor:
- test_register_does_not_leak_fake_defaults: SQLAlchemy'nin `university=None`
  atamasını modelin sahte default'uyla ("Doğuş Üniversitesi") sessizce
  değiştirmesi bug'ı.
- test_login_is_rate_limited_after_five_attempts: /auth/login'in daha önce
  hiç sınırlanmıyor olması bug'ı.
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
