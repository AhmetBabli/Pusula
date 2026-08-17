"""
E-posta ile onaylı başvuru gönderimi testleri.

Bu dosya, bu oturumda inşa edilen akışın disiplinini kilitliyor:
/prepare hiçbir zaman GÖNDERMEZ, sadece hazırlar; gönderim sadece
/{id}/approve ile onaylandıktan sonra /{id}/submit ile, ve sadece
OutreachAgent.send_via_account çağrılarak olur. E-posta bulunamayan
ilanlarda mevcut kopyala-yapıştır paketine sorunsuz düşülmesi de
buradan kilitleniyor.

Gerçek Gemini/DuckDuckGo/Gmail çağrıları burada hiç yapılmaz — hepsi mock'lanır.
"""
from backend.tests.conftest import register_and_login
from backend.models.user import UserProfile
from backend.models.cv import CV
from backend.models.job import Job
from backend.models.inbox import EmailAccount


def _auth_headers(client, email="apptest@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def _seed_cv_and_job(db_session, email, source_url="https://example.com/ilan/1"):
    user = db_session.query(UserProfile).filter(UserProfile.email == email).first()
    cv = CV(
        user_id=user.id,
        title="Test CV",
        variant_type="general",
        extracted_text="Python ve SQL bilgisi olan bir öğrenci.",
        is_default=True,
    )
    job = Job(
        source="kariyer_net",
        source_url=source_url,
        title="Yazılım Stajyeri",
        company="Test A.Ş.",
        description="Başvurular için iletişim: ik@sirket.com",
    )
    db_session.add_all([cv, job])
    db_session.commit()
    db_session.refresh(cv)
    db_session.refresh(job)
    return user, cv, job


def _mock_letter_and_email(monkeypatch, email="ik@sirket.com", source="job_posting", letter="Sayın İnsan Kaynakları..."):
    async def fake_generate_cover_letter(**kwargs):
        return letter

    async def fake_find_job_contact_email(job, **kwargs):
        return email, source

    monkeypatch.setattr("backend.ai.gemini_client.generate_cover_letter", fake_generate_cover_letter)
    monkeypatch.setattr(
        "backend.automation.outreach_agent.OutreachAgent.find_job_contact_email",
        fake_find_job_contact_email,
    )


def _prepare(client, headers, job_id, cv_id):
    return client.post("/api/applications/prepare", json={"job_id": job_id, "cv_id": cv_id}, headers=headers)


def test_prepare_finds_email_from_job_posting(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    res = _prepare(client, headers, job.id, cv.id)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "awaiting_approval"
    assert body["contact_email"] == "ik@sirket.com"
    assert body["contact_email_source"] == "job_posting"


def test_prepare_without_cv_returns_400(client, db_session):
    headers = _auth_headers(client)
    job = Job(source="kariyer_net", source_url="https://example.com/ilan/2", title="Stajyer", company="X A.Ş.")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    res = _prepare(client, headers, job.id, None)
    assert res.status_code == 400


def test_prepare_unknown_job_returns_404(client, db_session):
    headers = _auth_headers(client)
    res = _prepare(client, headers, 999, None)
    assert res.status_code == 404


def test_approve_lets_user_override_contact_email(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch, email="tahmin@sirket.com", source="company_site")

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]

    res = client.post(
        f"/api/applications/{app_id}/approve",
        json={"approved": True, "contact_email": "duzeltilmis@sirket.com"},
        headers=headers,
    )
    assert res.status_code == 200, res.text

    list_res = client.get("/api/applications/", headers=headers)
    app_out = next(a for a in list_res.json() if a["id"] == app_id)
    assert app_out["status"] == "approved"
    assert app_out["contact_email"] == "duzeltilmis@sirket.com"
    assert app_out["contact_email_source"] == "manual"


def test_reject_resets_status_to_draft(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]

    res = client.post(f"/api/applications/{app_id}/approve", json={"approved": False}, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "draft"


def test_submit_with_contact_email_sends_via_smtp(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)
    account = EmailAccount(user_id=user.id, email="sender@example.com")
    account.app_password = "fake-app-password"
    db_session.add(account)
    db_session.commit()

    send_calls = []
    monkeypatch.setattr(
        "backend.automation.outreach_agent.OutreachAgent.send_via_account",
        lambda **kwargs: send_calls.append(kwargs) or True,
    )

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    client.post(f"/api/applications/{app_id}/approve", json={"approved": True}, headers=headers)

    res = client.post(f"/api/applications/{app_id}/submit", headers=headers)

    assert res.status_code == 200, res.text
    assert res.json()["send_status"] == "sent"
    assert len(send_calls) == 1
    assert send_calls[0]["target_email"] == "ik@sirket.com"


def test_submit_without_email_account_returns_400(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    client.post(f"/api/applications/{app_id}/approve", json={"approved": True}, headers=headers)

    # Gmail hesabı hiç bağlanmamış — gönderim denenmemeli, açık bir 400 dönmeli.
    res = client.post(f"/api/applications/{app_id}/submit", headers=headers)
    assert res.status_code == 400


def test_submit_send_failure_keeps_approved_status_for_retry(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)
    account = EmailAccount(user_id=user.id, email="sender@example.com")
    account.app_password = "fake-app-password"
    db_session.add(account)
    db_session.commit()

    monkeypatch.setattr(
        "backend.automation.outreach_agent.OutreachAgent.send_via_account",
        lambda **kwargs: False,
    )

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    client.post(f"/api/applications/{app_id}/approve", json={"approved": True}, headers=headers)

    res = client.post(f"/api/applications/{app_id}/submit", headers=headers)
    assert res.status_code == 502

    # Başarısız gönderim sonrası kullanıcı "Tekrar Dene" yapabilsin diye
    # durum "approved" olarak kalmalı, "submitted" olarak işaretlenmemeli.
    list_res = client.get("/api/applications/", headers=headers)
    app_out = next(a for a in list_res.json() if a["id"] == app_id)
    assert app_out["status"] == "approved"
    assert app_out["send_status"] == "failed"
    assert app_out["send_error"]


def test_submit_without_findable_email_falls_back_to_copilot_package(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch, email="", source="")

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    client.post(f"/api/applications/{app_id}/approve", json={"approved": True}, headers=headers)

    res = client.post(f"/api/applications/{app_id}/submit", headers=headers)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["send_status"] == "not_applicable"
    assert "copilot_data" in body


def test_submit_requires_approval(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]

    # Henüz onaylanmadı (awaiting_approval) — gönderim reddedilmeli.
    res = client.post(f"/api/applications/{app_id}/submit", headers=headers)
    assert res.status_code == 400


def test_answer_questions_appends_without_overwriting(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    async def fake_generate_application_qa(**kwargs):
        return [{"question": q, "answer": f"Cevap: {q}"} for q in kwargs["custom_questions"]]

    monkeypatch.setattr("backend.ai.gemini_client.generate_application_qa", fake_generate_application_qa)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]

    res1 = client.post(
        f"/api/applications/{app_id}/answer-questions",
        json={"questions": ["Neden bizi seçtiniz?"]},
        headers=headers,
    )
    assert res1.status_code == 200, res1.text
    assert len(res1.json()["qa_answers"]) == 1

    res2 = client.post(
        f"/api/applications/{app_id}/answer-questions",
        json={"questions": ["Uzaktan çalışmaya uygun musunuz?"]},
        headers=headers,
    )
    assert res2.status_code == 200
    # İkinci çağrı birinciyi silmemeli, üzerine eklemeli.
    assert len(res2.json()["qa_answers"]) == 2


def test_answer_questions_rejects_empty_list(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]

    res = client.post(f"/api/applications/{app_id}/answer-questions", json={"questions": []}, headers=headers)
    assert res.status_code == 422


def test_submit_is_rate_limited_after_ten_per_hour(client, db_session, monkeypatch):
    """Regresyon testi: /submit gerçek bir e-posta gönderir, bu yüzden bir
    istemci hatası/döngüsü aynı IP'den onlarca gerçek e-posta göndermemeli.
    10/saat sonrası 429 dönmeli, önceki dokuz gönderim gerçek 200 almalı."""
    headers = _auth_headers(client)
    user, cv, _ = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)
    account = EmailAccount(user_id=user.id, email="sender@example.com")
    account.app_password = "fake-app-password"
    db_session.add(account)
    db_session.commit()
    monkeypatch.setattr(
        "backend.automation.outreach_agent.OutreachAgent.send_via_account",
        lambda **kwargs: True,
    )

    for i in range(11):
        job = Job(
            source="kariyer_net",
            source_url=f"https://example.com/ilan/rate-{i}",
            title="Yazılım Stajyeri",
            company="Test A.Ş.",
            description="Başvurular için iletişim: ik@sirket.com",
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
        client.post(f"/api/applications/{app_id}/approve", json={"approved": True}, headers=headers)

        res = client.post(f"/api/applications/{app_id}/submit", headers=headers)
        if i < 10:
            assert res.status_code == 200, res.text
        else:
            assert res.status_code == 429
