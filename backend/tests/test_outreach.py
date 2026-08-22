"""
Soğuk e-posta onay kapısı testleri.

Bu dosya, bu oturumda düzeltilen en kritik bug'ı regresyona karşı kilitliyor:
/outreach/prepare hiçbir şey GÖNDERMEMELİ, sadece taslak hazırlamalı. Gerçek
gönderim sadece kullanıcının açıkça çağırdığı /outreach/{id}/send üzerinden,
ve sadece OutreachAgent.send_via_account çağrılarak olmalı.

Gerçek Gemini/DuckDuckGo/Gmail çağrıları burada hiç yapılmaz — hepsi mock'lanır.
"""
from backend.tests.conftest import register_and_login
from backend.models.user import UserProfile
from backend.models.cv import CV
from backend.models.inbox import EmailAccount


def _auth_headers(client, email="outreach@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def _seed_cv_and_account(db_session, email):
    user = db_session.query(UserProfile).filter(UserProfile.email == email).first()
    cv = CV(
        user_id=user.id,
        title="Test CV",
        variant_type="general",
        extracted_text="Python ve SQL bilgisi olan bir öğrenci.",
        is_default=True,
    )
    db_session.add(cv)
    account = EmailAccount(user_id=user.id, email="sender@example.com")
    account.app_password = "fake-app-password"
    db_session.add(account)
    db_session.commit()
    return user


def _mock_ai_and_hunt(monkeypatch, target_email="ik@sirket.com", draft_body="Merhaba, başvurmak istiyorum."):
    async def fake_hunt_email(company_name, **kwargs):
        return target_email

    monkeypatch.setattr("backend.routers.outreach.OutreachAgent.hunt_email", fake_hunt_email)

    async def fake_generate_cold_email(**kwargs):
        return draft_body

    monkeypatch.setattr("backend.routers.outreach.generate_cold_email", fake_generate_cold_email)


def test_prepare_creates_draft_and_does_not_send(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    _seed_cv_and_account(db_session, "outreach@example.com")
    _mock_ai_and_hunt(monkeypatch)

    send_calls = []
    monkeypatch.setattr(
        "backend.routers.outreach.OutreachAgent.send_via_account",
        lambda **kwargs: send_calls.append(kwargs) or True,
    )

    res = client.post("/api/outreach/prepare", json={"company_name": "Test Şirketi"}, headers=headers)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "awaiting_approval"
    assert body["target_email"] == "ik@sirket.com"
    assert body["body"] == "Merhaba, başvurmak istiyorum."
    # KRİTİK: prepare hiçbir gönderim fonksiyonunu çağırmamalı.
    assert send_calls == []


def test_prepare_surfaces_ai_failure_instead_of_sending_error_string(client, db_session, monkeypatch):
    """generate_cold_email eskiden hata durumunda "[Hata] ..." metnini
    döndürüyordu; bu metin 200 OK ile taslak olarak kaydedilip kullanıcı
    onayladığında gerçek bir şirkete e-posta olarak gidiyordu (geri
    alınamaz dış etki). Artık gerçek hatayı fırlatıyor, /prepare 503
    dönmeli — sahte bir taslak asla oluşturulmamalı."""
    from backend.exceptions import AIServiceError

    headers = _auth_headers(client)
    _seed_cv_and_account(db_session, "outreach@example.com")

    async def fake_hunt_email(company_name, **kwargs):
        return "ik@sirket.com"

    async def fake_generate_cold_email_fails(**kwargs):
        raise AIServiceError("AI service temporarily unavailable")

    monkeypatch.setattr("backend.routers.outreach.OutreachAgent.hunt_email", fake_hunt_email)
    monkeypatch.setattr("backend.routers.outreach.generate_cold_email", fake_generate_cold_email_fails)

    res = client.post("/api/outreach/prepare", json={"company_name": "Test Şirketi"}, headers=headers)
    assert res.status_code == 503
    assert "[Hata]" not in res.text


def test_prepare_without_findable_email_returns_404(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    _seed_cv_and_account(db_session, "outreach@example.com")
    async def fake_hunt_email_empty(company_name, **kwargs):
        return ""

    monkeypatch.setattr("backend.routers.outreach.OutreachAgent.hunt_email", fake_hunt_email_empty)

    res = client.post("/api/outreach/prepare", json={"company_name": "Bulunamayan Şirket"}, headers=headers)
    assert res.status_code == 404


def test_prepare_without_cv_returns_400(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user = db_session.query(UserProfile).filter(UserProfile.email == "outreach@example.com").first()
    account = EmailAccount(user_id=user.id, email="sender@example.com")
    account.app_password = "fake-app-password"
    db_session.add(account)
    db_session.commit()

    res = client.post("/api/outreach/prepare", json={"company_name": "Test Şirketi"}, headers=headers)
    assert res.status_code == 400


def test_prepare_without_email_account_returns_404(client, db_session):
    headers = _auth_headers(client)
    user = db_session.query(UserProfile).filter(UserProfile.email == "outreach@example.com").first()
    cv = CV(user_id=user.id, title="Test CV", variant_type="general", extracted_text="Metin", is_default=True)
    db_session.add(cv)
    db_session.commit()

    res = client.post("/api/outreach/prepare", json={"company_name": "Test Şirketi"}, headers=headers)
    assert res.status_code == 404


def test_send_requires_existing_draft(client, db_session):
    headers = _auth_headers(client)
    _seed_cv_and_account(db_session, "outreach@example.com")

    res = client.post("/api/outreach/999/send", json={"target_email": None}, headers=headers)
    assert res.status_code == 404


def test_send_success_marks_sent(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    _seed_cv_and_account(db_session, "outreach@example.com")
    _mock_ai_and_hunt(monkeypatch)
    monkeypatch.setattr("backend.routers.outreach.OutreachAgent.send_via_account", lambda **kwargs: True)

    prepare_res = client.post("/api/outreach/prepare", json={"company_name": "Test Şirketi"}, headers=headers)
    draft_id = prepare_res.json()["id"]

    send_res = client.post(f"/api/outreach/{draft_id}/send", json={"target_email": None}, headers=headers)
    assert send_res.status_code == 200, send_res.text
    assert send_res.json()["status"] == "sent"


def test_send_can_override_target_email(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    _seed_cv_and_account(db_session, "outreach@example.com")
    _mock_ai_and_hunt(monkeypatch, target_email="tahmin@sirket.com")

    captured = {}

    def fake_send(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr("backend.routers.outreach.OutreachAgent.send_via_account", fake_send)

    prepare_res = client.post("/api/outreach/prepare", json={"company_name": "Test Şirketi"}, headers=headers)
    draft_id = prepare_res.json()["id"]

    send_res = client.post(f"/api/outreach/{draft_id}/send", json={"target_email": "duzeltilmis@sirket.com"}, headers=headers)
    assert send_res.status_code == 200
    assert send_res.json()["target_email"] == "duzeltilmis@sirket.com"
    assert captured["target_email"] == "duzeltilmis@sirket.com"


def test_send_failure_marks_failed(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    _seed_cv_and_account(db_session, "outreach@example.com")
    _mock_ai_and_hunt(monkeypatch)
    monkeypatch.setattr("backend.routers.outreach.OutreachAgent.send_via_account", lambda **kwargs: False)

    prepare_res = client.post("/api/outreach/prepare", json={"company_name": "Test Şirketi"}, headers=headers)
    draft_id = prepare_res.json()["id"]

    send_res = client.post(f"/api/outreach/{draft_id}/send", json={"target_email": None}, headers=headers)
    assert send_res.status_code == 502

    # Başarısız olsa bile taslak veritabanında "failed" olarak kalmalı, kaybolmamalı.
    get_res = client.post(f"/api/outreach/{draft_id}/send", json={"target_email": None}, headers=headers)
    assert get_res.status_code == 502  # Tekrar denenebilir, "zaten gönderildi" hatası vermemeli
