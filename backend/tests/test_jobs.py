"""
Kullanıcı bazlı ilan durumu (JobUserState) regresyon testleri.

Bu dosya, tam olarak düzeltilen bug'ı kilitliyor: status/is_favorite/
match_score önceden paylaşılan Job satırında tutuluyordu — iki kullanıcı
aynı ilanı favorileyip başvurunca birbirinin durumunu eziyordu. Artık
kullanıcı bazlı JobUserState'te tutuluyor, bu testler iki farklı
kullanıcının aynı ilan üzerinde birbirinden tamamen bağımsız durumlara
sahip olabildiğini doğruluyor.
"""
from backend.tests.conftest import register_and_login
from backend.models.job import Job


def _auth_headers(client, email):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def _seed_job(db_session, source_url="https://example.com/ilan/shared-1"):
    job = Job(
        source="kariyer_net",
        source_url=source_url,
        title="Yazılım Stajyeri",
        company="Paylaşılan A.Ş.",
        description="Python bilgisi olan stajyer aranıyor.",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_favorite_does_not_leak_between_users(client, db_session):
    job = _seed_job(db_session)
    headers_a = _auth_headers(client, "user-a@example.com")
    headers_b = _auth_headers(client, "user-b@example.com")

    # A favoriler, B hiç dokunmaz.
    res = client.patch(f"/api/jobs/{job.id}/favorite", headers=headers_a)
    assert res.status_code == 200
    assert res.json()["is_favorite"] is True

    list_a = client.get("/api/jobs/", headers=headers_a).json()
    list_b = client.get("/api/jobs/", headers=headers_b).json()

    job_a = next(j for j in list_a if j["id"] == job.id)
    job_b = next(j for j in list_b if j["id"] == job.id)

    assert job_a["is_favorite"] is True
    assert job_b["is_favorite"] is False  # B'nin durumu A'dan hiç etkilenmemeli


def test_status_does_not_leak_between_users(client, db_session):
    job = _seed_job(db_session, source_url="https://example.com/ilan/shared-2")
    headers_a = _auth_headers(client, "user-a2@example.com")
    headers_b = _auth_headers(client, "user-b2@example.com")

    client.patch(f"/api/jobs/{job.id}/status", json={"status": "applied"}, headers=headers_a)

    detail_a = client.get(f"/api/jobs/{job.id}", headers=headers_a).json()
    detail_b = client.get(f"/api/jobs/{job.id}", headers=headers_b).json()

    assert detail_a["status"] == "applied"
    assert detail_b["status"] == "new"  # B hiç dokunmadı, varsayılanda kalmalı


def test_match_score_is_per_user(client, db_session, monkeypatch):
    job = _seed_job(db_session, source_url="https://example.com/ilan/shared-3")
    headers_a = _auth_headers(client, "user-a3@example.com")
    headers_b = _auth_headers(client, "user-b3@example.com")

    from backend.models.user import UserProfile
    from backend.models.cv import CV

    for email in ("user-a3@example.com", "user-b3@example.com"):
        user = db_session.query(UserProfile).filter(UserProfile.email == email).first()
        cv = CV(user_id=user.id, title="CV", variant_type="general", extracted_text="metin", is_default=True)
        db_session.add(cv)
    db_session.commit()

    scores = iter([90.0, 40.0])

    async def fake_match_job_to_cv(*args, **kwargs):
        return {"score": next(scores), "explanation": "test", "missing_skills": []}

    monkeypatch.setattr("backend.routers.jobs.match_job_to_cv", fake_match_job_to_cv)

    res_a = client.post(f"/api/jobs/{job.id}/match", headers=headers_a)
    res_b = client.post(f"/api/jobs/{job.id}/match", headers=headers_b)
    assert res_a.status_code == 200, res_a.text
    assert res_b.status_code == 200, res_b.text

    detail_a = client.get(f"/api/jobs/{job.id}", headers=headers_a).json()
    detail_b = client.get(f"/api/jobs/{job.id}", headers=headers_b).json()

    # İKİNCİ eşleştirme (B) BİRİNCİYİ (A) EZMEMELİ — bug tam olarak buydu.
    assert detail_a["match_score"] == 90.0
    assert detail_b["match_score"] == 40.0


def test_unmatched_job_has_default_state(client, db_session):
    job = _seed_job(db_session, source_url="https://example.com/ilan/shared-4")
    headers = _auth_headers(client, "user-c@example.com")

    detail = client.get(f"/api/jobs/{job.id}", headers=headers).json()
    assert detail["status"] == "new"
    assert detail["is_favorite"] is False
    assert detail["match_score"] == 0


def test_list_jobs_filters_by_own_status(client, db_session):
    job1 = _seed_job(db_session, source_url="https://example.com/ilan/shared-5")
    job2 = _seed_job(db_session, source_url="https://example.com/ilan/shared-6")
    headers = _auth_headers(client, "user-d@example.com")

    client.patch(f"/api/jobs/{job1.id}/status", json={"status": "applied"}, headers=headers)

    applied = client.get("/api/jobs/", params={"status": "applied"}, headers=headers).json()
    new_ones = client.get("/api/jobs/", params={"status": "new"}, headers=headers).json()

    assert [j["id"] for j in applied] == [job1.id]
    assert job2.id in [j["id"] for j in new_ones]
    assert job1.id not in [j["id"] for j in new_ones]


def test_run_job_sync_matches_per_user(client, db_session, db_engine, monkeypatch):
    """run_job_sync() en çok değiştirilen (ve doğrudan test edilmeyen) kod
    yolu — scraper'ları ve Gemini'yi mock'layıp gerçekten CV'si olan HER
    kullanıcı için ayrı bir JobUserState satırı ürettiğini doğruluyor."""
    import backend.routers.jobs as jobs_module
    from sqlalchemy.orm import sessionmaker
    from backend.models.user import UserProfile
    from backend.models.cv import CV
    from backend.models.job_user_state import JobUserState

    # run_job_sync() kendi SessionLocal()'ını açıyor — test'in izole
    # in-memory motoruna yönlendiriyoruz, gerçek dev DB'ye dokunmasın.
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr(jobs_module, "SessionLocal", TestSessionLocal)

    token_a = register_and_login(client, email="sync-a@example.com")
    token_b = register_and_login(client, email="sync-b@example.com")
    user_a = db_session.query(UserProfile).filter(UserProfile.email == "sync-a@example.com").first()
    user_b = db_session.query(UserProfile).filter(UserProfile.email == "sync-b@example.com").first()
    db_session.add(CV(user_id=user_a.id, title="CV A", variant_type="general", extracted_text="Python", is_default=True))
    db_session.add(CV(user_id=user_b.id, title="CV B", variant_type="general", extracted_text="React", is_default=True))
    db_session.commit()

    fake_job = {
        "title": "Yazılım Stajyeri",
        "company": "Sync Test A.Ş.",
        "location": "İstanbul",
        "source_url": "https://example.com/ilan/sync-1",
        "description": "Python bilen stajyer aranıyor.",
        "requirements": "Python",
        "source": "arbeitnow",
        "job_type": "staj",
    }

    # isinstance() ile dallanıldığı için sınıfların kendisini (kimliğini) değil,
    # sadece scrape_jobs metodlarını mock'luyoruz — biri sync (to_thread ile
    # çağrılıyor), KariyerNetScraper'ınki ise doğrudan await edilen async.
    from backend.scrapers.youthall_scraper import YouthallScraper
    from backend.scrapers.kariyer_net_scraper import KariyerNetScraper
    from backend.scrapers.linkedin_scraper import LinkedInScraper
    from backend.scrapers.arbeitnow_scraper import ArbeitnowScraper

    monkeypatch.setattr(YouthallScraper, "scrape_jobs", lambda self, **kwargs: [fake_job])
    monkeypatch.setattr(LinkedInScraper, "scrape_jobs", lambda self, **kwargs: [])
    monkeypatch.setattr(ArbeitnowScraper, "scrape_jobs", lambda self, **kwargs: [])

    async def fake_kariyer_net_scrape(self, **kwargs):
        return []

    monkeypatch.setattr(KariyerNetScraper, "scrape_jobs", fake_kariyer_net_scrape)

    async def fake_match_jobs_batch(jobs_payload, cv_text, skills, api_key=None):
        score = 77.0 if "Python" in cv_text else 33.0
        return {j["id"]: {"score": score, "explanation": "test", "missing_skills": [], "ai_powered": True} for j in jobs_payload}

    monkeypatch.setattr(jobs_module, "match_jobs_batch", fake_match_jobs_batch)

    import asyncio
    asyncio.run(jobs_module.run_job_sync())

    job = db_session.query(jobs_module.Job).filter(jobs_module.Job.source_url == fake_job["source_url"]).first()
    assert job is not None

    state_a = db_session.query(JobUserState).filter(JobUserState.user_id == user_a.id, JobUserState.job_id == job.id).first()
    state_b = db_session.query(JobUserState).filter(JobUserState.user_id == user_b.id, JobUserState.job_id == job.id).first()
    assert state_a.match_score == 77.0
    assert state_b.match_score == 33.0
