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


def _mock_letter_and_email(monkeypatch, email="ik@sirket.com", source="job_posting", letter="Sayın İnsan Kaynakları...", source_url=""):
    async def fake_generate_cover_letter(**kwargs):
        return letter

    async def fake_find_job_contact_email(job, **kwargs):
        return email, source, source_url

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


# ─── Mezun/Referans Bulucu ───

def test_find_referrals_returns_candidates(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    user.university = "Doğuş Üniversitesi"
    db_session.commit()
    _mock_letter_and_email(monkeypatch)

    fake_candidates = [
        {"name": "Ayşe Yılmaz", "title": "Yazılım Mühendisi", "search_hint": "site:linkedin.com/in Ayşe Yılmaz Test A.Ş.", "message_draft": "Merhaba Ayşe,..."},
    ]

    async def fake_find_alumni_referrals(**kwargs):
        assert kwargs["university"] == "Doğuş Üniversitesi"
        assert kwargs["company_name"] == "Test A.Ş."
        return fake_candidates

    monkeypatch.setattr("backend.ai.gemini_client.find_alumni_referrals", fake_find_alumni_referrals)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    res = client.post(f"/api/applications/{app_id}/find-referrals", headers=headers)

    assert res.status_code == 200, res.text
    assert res.json()["referral_candidates"] == fake_candidates

    # Sonuç Application'a yazılmış olmalı, listelemede de görünmeli.
    listed = client.get("/api/applications/", headers=headers).json()
    app_out = next(a for a in listed if a["id"] == app_id)
    assert app_out["referral_candidates"] == fake_candidates


def test_find_referrals_requires_university(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    res = client.post(f"/api/applications/{app_id}/find-referrals", headers=headers)
    assert res.status_code == 400


# ─── Başvuru Sonrası Takip Nudge'ı ───

def _submit_with_real_email(client, headers, db_session, user_id, job, cv, monkeypatch):
    _mock_letter_and_email(monkeypatch)
    account = EmailAccount(user_id=user_id, email="sender@example.com")
    account.app_password = "fake-app-password"
    db_session.add(account)
    db_session.commit()
    monkeypatch.setattr("backend.automation.outreach_agent.OutreachAgent.send_via_account", lambda **kwargs: True)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    client.post(f"/api/applications/{app_id}/approve", json={"approved": True}, headers=headers)
    client.post(f"/api/applications/{app_id}/submit", headers=headers)
    return app_id


def test_draft_followup_requires_sent_email(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch, email="", source="")

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]
    client.post(f"/api/applications/{app_id}/approve", json={"approved": True}, headers=headers)
    client.post(f"/api/applications/{app_id}/submit", headers=headers)  # e-postasız -> kopyala-yapıştır

    res = client.post(f"/api/applications/{app_id}/draft-followup", headers=headers)
    assert res.status_code == 400


def test_followup_not_eligible_before_ten_days(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    app_id = _submit_with_real_email(client, headers, db_session, user.id, job, cv, monkeypatch)

    listed = client.get("/api/applications/", headers=headers).json()
    app_out = next(a for a in listed if a["id"] == app_id)
    assert app_out["followup_eligible"] is False  # az önce gönderildi


def test_followup_eligible_after_ten_days_and_full_flow(client, db_session, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from backend.models.application import Application

    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    app_id = _submit_with_real_email(client, headers, db_session, user.id, job, cv, monkeypatch)

    # 10+ gün önce gönderilmiş gibi göster
    app = db_session.query(Application).filter(Application.id == app_id).first()
    app.submitted_at = datetime.now(timezone.utc) - timedelta(days=11)
    db_session.commit()

    listed = client.get("/api/applications/", headers=headers).json()
    app_out = next(a for a in listed if a["id"] == app_id)
    assert app_out["followup_eligible"] is True

    async def fake_generate_followup_email(**kwargs):
        assert kwargs["days_since_submitted"] >= 11
        return "Sayın İlgili, başvurumla ilgili..."

    monkeypatch.setattr("backend.ai.gemini_client.generate_followup_email", fake_generate_followup_email)

    draft_res = client.post(f"/api/applications/{app_id}/draft-followup", headers=headers)
    assert draft_res.status_code == 200, draft_res.text
    draft_body = draft_res.json()["draft"]

    monkeypatch.setattr("backend.automation.outreach_agent.OutreachAgent.send_via_account", lambda **kwargs: True)
    send_res = client.post(f"/api/applications/{app_id}/send-followup", json={"body": draft_body}, headers=headers)
    assert send_res.status_code == 200, send_res.text

    # Takip gönderildikten sonra nudge bir daha önerilmemeli.
    listed_after = client.get("/api/applications/", headers=headers).json()
    app_after = next(a for a in listed_after if a["id"] == app_id)
    assert app_after["followup_eligible"] is False


def test_mark_responded_stops_followup_eligibility(client, db_session, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from backend.models.application import Application

    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    app_id = _submit_with_real_email(client, headers, db_session, user.id, job, cv, monkeypatch)

    app = db_session.query(Application).filter(Application.id == app_id).first()
    app.submitted_at = datetime.now(timezone.utc) - timedelta(days=11)
    db_session.commit()

    res = client.post(f"/api/applications/{app_id}/mark-responded", headers=headers)
    assert res.status_code == 200, res.text

    listed = client.get("/api/applications/", headers=headers).json()
    app_out = next(a for a in listed if a["id"] == app_id)
    assert app_out["followup_eligible"] is False


# ─── Gerçek Sonuç Takibi (interview/offer/rejected) ───

def test_update_outcome_to_interview(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    app_id = _submit_with_real_email(client, headers, db_session, user.id, job, cv, monkeypatch)

    res = client.patch(f"/api/applications/{app_id}/outcome", json={"outcome": "interview"}, headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "interview"

    listed = client.get("/api/applications/", headers=headers).json()
    app_out = next(a for a in listed if a["id"] == app_id)
    assert app_out["status"] == "interview"
    # Sonuç bildirmek bir yanıt geldiği anlamına gelir -> takip nudge'ı susmalı.
    assert app_out["followup_eligible"] is False


def test_update_outcome_rejects_invalid_value(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    app_id = _submit_with_real_email(client, headers, db_session, user.id, job, cv, monkeypatch)

    res = client.patch(f"/api/applications/{app_id}/outcome", json={"outcome": "maybe"}, headers=headers)
    assert res.status_code == 422


def test_update_outcome_requires_submitted_application(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    _mock_letter_and_email(monkeypatch)

    app_id = _prepare(client, headers, job.id, cv.id).json()["application_id"]  # hâlâ awaiting_approval
    res = client.patch(f"/api/applications/{app_id}/outcome", json={"outcome": "interview"}, headers=headers)
    assert res.status_code == 400


def test_update_outcome_progression_interview_to_offer(client, db_session, monkeypatch):
    headers = _auth_headers(client)
    user, cv, job = _seed_cv_and_job(db_session, "apptest@example.com")
    app_id = _submit_with_real_email(client, headers, db_session, user.id, job, cv, monkeypatch)

    client.patch(f"/api/applications/{app_id}/outcome", json={"outcome": "interview"}, headers=headers)
    res = client.patch(f"/api/applications/{app_id}/outcome", json={"outcome": "offer"}, headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "offer"
