"""
CV varyant performans analitiği testleri (/dashboard/stats::cv_variant_performance).

(1) numaralı borç düzeltmesiyle match_score kullanıcıya özel hale geldiği
için mümkün oldu — bu testler agregasyonun doğru varyant tipine göre
gruplandığını ve başka kullanıcının verisini karıştırmadığını doğruluyor.
"""
from backend.tests.conftest import register_and_login
from backend.models.user import UserProfile
from backend.models.cv import CV
from backend.models.job import Job
from backend.models.job_user_state import JobUserState
from backend.models.application import Application


def _auth_headers(client, email):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def test_cv_variant_performance_groups_correctly(client, db_session):
    headers = _auth_headers(client, "perf@example.com")
    user = db_session.query(UserProfile).filter(UserProfile.email == "perf@example.com").first()

    cv_general = CV(user_id=user.id, title="Genel CV", variant_type="general", extracted_text="metin", is_default=True)
    cv_cyber = CV(user_id=user.id, title="Siber CV", variant_type="cyber", extracted_text="metin")
    db_session.add_all([cv_general, cv_cyber])
    db_session.flush()

    job1 = Job(source="kariyer_net", source_url="https://example.com/perf-1", title="İlan 1", company="A")
    job2 = Job(source="kariyer_net", source_url="https://example.com/perf-2", title="İlan 2", company="B")
    job3 = Job(source="kariyer_net", source_url="https://example.com/perf-3", title="İlan 3", company="C")
    db_session.add_all([job1, job2, job3])
    db_session.flush()

    # general CV: iki eşleşme (80, 60) -> ortalama 70
    db_session.add(JobUserState(user_id=user.id, job_id=job1.id, match_score=80.0, best_cv_id=cv_general.id))
    db_session.add(JobUserState(user_id=user.id, job_id=job2.id, match_score=60.0, best_cv_id=cv_general.id))
    # cyber CV: bir eşleşme (40)
    db_session.add(JobUserState(user_id=user.id, job_id=job3.id, match_score=40.0, best_cv_id=cv_cyber.id))

    # general CV ile bir başvuru yapılmış
    db_session.add(Application(user_id=user.id, job_id=job1.id, cv_id=cv_general.id, status="submitted"))
    db_session.commit()

    res = client.get("/api/dashboard/stats", headers=headers)
    assert res.status_code == 200, res.text
    perf = {row["variant_type"]: row for row in res.json()["cv_variant_performance"]}

    assert perf["general"]["cv_count"] == 1
    assert perf["general"]["application_count"] == 1
    assert perf["general"]["matched_job_count"] == 2
    assert perf["general"]["avg_match_score"] == 70.0

    assert perf["cyber"]["cv_count"] == 1
    assert perf["cyber"]["application_count"] == 0
    assert perf["cyber"]["matched_job_count"] == 1
    assert perf["cyber"]["avg_match_score"] == 40.0


def test_cv_variant_performance_is_per_user(client, db_session):
    """İki farklı kullanıcı aynı ilanlarda farklı CV'lerle eşleşse bile
    birbirinin performans istatistiklerini görmemeli/etkilememeli."""
    headers_a = _auth_headers(client, "perf-a@example.com")
    headers_b = _auth_headers(client, "perf-b@example.com")
    user_a = db_session.query(UserProfile).filter(UserProfile.email == "perf-a@example.com").first()
    user_b = db_session.query(UserProfile).filter(UserProfile.email == "perf-b@example.com").first()

    cv_a = CV(user_id=user_a.id, title="CV A", variant_type="general", extracted_text="metin", is_default=True)
    cv_b = CV(user_id=user_b.id, title="CV B", variant_type="general", extracted_text="metin", is_default=True)
    db_session.add_all([cv_a, cv_b])
    db_session.flush()

    job = Job(source="kariyer_net", source_url="https://example.com/perf-shared", title="İlan", company="A")
    db_session.add(job)
    db_session.flush()

    db_session.add(JobUserState(user_id=user_a.id, job_id=job.id, match_score=90.0, best_cv_id=cv_a.id))
    db_session.add(JobUserState(user_id=user_b.id, job_id=job.id, match_score=10.0, best_cv_id=cv_b.id))
    db_session.commit()

    res_a = client.get("/api/dashboard/stats", headers=headers_a).json()
    res_b = client.get("/api/dashboard/stats", headers=headers_b).json()

    perf_a = {row["variant_type"]: row for row in res_a["cv_variant_performance"]}
    perf_b = {row["variant_type"]: row for row in res_b["cv_variant_performance"]}

    assert perf_a["general"]["avg_match_score"] == 90.0
    assert perf_b["general"]["avg_match_score"] == 10.0


def test_cv_variant_performance_empty_when_no_cvs(client):
    headers = _auth_headers(client, "perf-empty@example.com")
    res = client.get("/api/dashboard/stats", headers=headers)
    assert res.status_code == 200
    assert res.json()["cv_variant_performance"] == []
