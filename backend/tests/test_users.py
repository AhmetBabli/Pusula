"""
Kullanıcı profili (users router) testleri.
"""
from sqlalchemy import text
from backend.tests.conftest import register_and_login


def _auth_headers(client, email="usertest@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def test_get_profile_returns_own_data_without_password(client):
    headers = _auth_headers(client, "profile-get@example.com")
    res = client.get("/api/users/profile", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "profile-get@example.com"
    assert "hashed_password" not in body
    assert "gemini_api_key" not in body
    assert body["has_gemini_api_key"] is False


def test_update_profile_persists_fields(client):
    headers = _auth_headers(client, "profile-update@example.com")
    res = client.patch(
        "/api/users/profile",
        json={
            "university": "Doğuş Üniversitesi",
            "department": "Yönetim Bilişim Sistemleri",
            "skills": ["Python", "SQL"],
            "graduation_year": 2026,
        },
        headers=headers,
    )
    assert res.status_code == 200

    profile = client.get("/api/users/profile", headers=headers).json()
    assert profile["university"] == "Doğuş Üniversitesi"
    assert profile["department"] == "Yönetim Bilişim Sistemleri"
    assert profile["skills"] == ["Python", "SQL"]
    assert profile["graduation_year"] == 2026


def test_update_profile_gemini_key_reflected_in_has_key_flag(client):
    headers = _auth_headers(client, "profile-key@example.com")

    before = client.get("/api/users/profile", headers=headers).json()
    assert before["has_gemini_api_key"] is False

    res = client.patch("/api/users/profile", json={"gemini_api_key": "test-anahtar-123"}, headers=headers)
    assert res.status_code == 200

    after = client.get("/api/users/profile", headers=headers).json()
    assert after["has_gemini_api_key"] is True
    assert "gemini_api_key" not in after  # ham anahtar asla API yanıtına sızmamalı


def test_update_profile_partial_update_does_not_clear_other_fields(client):
    headers = _auth_headers(client, "profile-partial@example.com")
    client.patch("/api/users/profile", json={"university": "Doğuş Üniversitesi"}, headers=headers)

    res = client.patch("/api/users/profile", json={"department": "YBS"}, headers=headers)
    assert res.status_code == 200

    profile = client.get("/api/users/profile", headers=headers).json()
    assert profile["university"] == "Doğuş Üniversitesi"  # önceki PATCH'ten korunmalı
    assert profile["department"] == "YBS"


def test_profile_requires_authentication(client):
    res = client.get("/api/users/profile")
    assert res.status_code == 401


def test_update_profile_persists_linkedin_data(client):
    headers = _auth_headers(client, "profile-linkedin@example.com")
    raw = "Deneyim:\nX Şirketi - Stajyer\n\nBeceriler:\nPython, SQL"

    res = client.patch("/api/users/profile", json={"linkedin_data": raw}, headers=headers)
    assert res.status_code == 200

    profile = client.get("/api/users/profile", headers=headers).json()
    assert profile["linkedin_data"] == raw


def test_update_profile_persists_work_experiences_and_certificates(client):
    headers = _auth_headers(client, "profile-experience@example.com")
    work_experiences = [
        {"title": "Yazılım Stajyeri", "company": "X Teknoloji", "start_date": "2025-06", "end_date": "2025-08", "current": False, "description": "Backend API geliştirme."},
        {"title": "Junior Developer", "company": "Y A.Ş.", "start_date": "2025-09", "end_date": "", "current": True, "description": ""},
    ]
    certificates = [
        {"name": "AWS Cloud Practitioner", "issuer": "Amazon", "date": "2025-03"},
    ]

    res = client.patch(
        "/api/users/profile",
        json={"work_experiences": work_experiences, "certificates": certificates},
        headers=headers,
    )
    assert res.status_code == 200

    profile = client.get("/api/users/profile", headers=headers).json()
    assert profile["work_experiences"] == work_experiences
    assert profile["certificates"] == certificates


def test_get_profile_handles_legacy_null_list_columns(client, db_engine):
    """work_experiences/certificates ALTER TABLE ile sonradan eklendiğinde var
    olan satırlarda NULL kalır (SQLAlchemy'nin Column(default=list)'i sadece
    ORM'in kendi INSERT'inde devreye girer) — bu gerçek bir hesapta /profile'ı
    500 ResponseValidationError ile kırmıştı. NULL geldiğinde boş listeye
    düşülmeli, hataya değil."""
    headers = _auth_headers(client, "profile-legacy-null@example.com")

    with db_engine.connect() as conn:
        conn.execute(
            text("UPDATE user_profiles SET work_experiences = NULL, certificates = NULL WHERE email = :email"),
            {"email": "profile-legacy-null@example.com"},
        )
        conn.commit()

    res = client.get("/api/users/profile", headers=headers)
    assert res.status_code == 200
    assert res.json()["work_experiences"] == []
    assert res.json()["certificates"] == []
