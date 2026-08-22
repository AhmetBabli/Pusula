"""
CV yönetimi (cvs router) testleri.

Kullanıcı izolasyonu, varsayılan-CV değişimi ve arka planda çalışan ATS
analizinin gerçekten DB'ye yazdığını kilitler. background_ats_analysis
kendi SessionLocal()'ını açtığı için (Depends(get_db) override'ından
etkilenmez) — test'in izole in-memory motoruna monkeypatch ile yönlendiriliyor,
gerçek dev DB'ye asla dokunmuyor (bkz. test_jobs.py::test_run_job_sync_matches_per_user).
"""
from sqlalchemy.orm import sessionmaker

from backend.tests.conftest import register_and_login
from backend.models.user import UserProfile
from backend.models.cv import CV


def _auth_headers(client, email="cvtest@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def _seed_cv(db_session, email, **kwargs):
    user = db_session.query(UserProfile).filter(UserProfile.email == email).first()
    cv = CV(user_id=user.id, title=kwargs.pop("title", "Test CV"), variant_type=kwargs.pop("variant_type", "general"), **kwargs)
    db_session.add(cv)
    db_session.commit()
    db_session.refresh(cv)
    return cv


def test_list_cvs_only_returns_own(client, db_session):
    headers_a = _auth_headers(client, "cv-a@example.com")
    headers_b = _auth_headers(client, "cv-b@example.com")
    _seed_cv(db_session, "cv-a@example.com", title="A'nın CV'si")
    _seed_cv(db_session, "cv-b@example.com", title="B'nin CV'si")

    list_a = client.get("/api/cvs/", headers=headers_a).json()
    list_b = client.get("/api/cvs/", headers=headers_b).json()

    assert [c["title"] for c in list_a] == ["A'nın CV'si"]
    assert [c["title"] for c in list_b] == ["B'nin CV'si"]


def test_list_cvs_handles_fractional_ats_score(client, db_session):
    """ats_score veritabanında Float — Gemini 87.5 gibi ondalıklı bir puan
    döndürdüğünde CVOut.ats_score (eskiden Optional[int]) Pydantic
    doğrulamasını reddedip /cvs/ ucunu kalıcı olarak 500'e düşürüyordu."""
    headers = _auth_headers(client, "cv-fractional-score@example.com")
    _seed_cv(db_session, "cv-fractional-score@example.com", ats_score=87.5)

    res = client.get("/api/cvs/", headers=headers)
    assert res.status_code == 200
    assert res.json()[0]["ats_score"] == 87.5


def test_download_cv_pdf_requires_ownership(client, db_session, tmp_path):
    """Eskiden /agents/cv/export-pdf/{session_id} istemcinin seçtiği bir
    session_id'ye göre dosya sunuyordu, sahiplik doğrulamıyordu (IDOR) —
    herhangi bir kullanıcı başkasının CV PDF'ini tahmin edip indirebiliyordu.
    Yeni /cvs/{cv_id}/pdf ucu _get_own_cv_or_404 ile korunuyor."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

    headers_owner = _auth_headers(client, "cv-pdf-owner@example.com")
    headers_intruder = _auth_headers(client, "cv-pdf-intruder@example.com")
    cv = _seed_cv(db_session, "cv-pdf-owner@example.com", file_path=str(pdf_file))

    res_owner = client.get(f"/api/cvs/{cv.id}/pdf", headers=headers_owner)
    assert res_owner.status_code == 200
    assert res_owner.headers["content-type"] == "application/pdf"

    res_intruder = client.get(f"/api/cvs/{cv.id}/pdf", headers=headers_intruder)
    assert res_intruder.status_code == 404


def test_get_cv_404_for_other_users_cv(client, db_session):
    headers_a = _auth_headers(client, "cv-owner@example.com")
    headers_b = _auth_headers(client, "cv-intruder@example.com")
    cv = _seed_cv(db_session, "cv-owner@example.com")

    res_owner = client.get(f"/api/cvs/{cv.id}", headers=headers_a)
    res_intruder = client.get(f"/api/cvs/{cv.id}", headers=headers_b)

    assert res_owner.status_code == 200
    assert res_intruder.status_code == 404


def test_generate_cv_creates_ai_generated_cv(client, monkeypatch):
    headers = _auth_headers(client, "cv-gen@example.com")

    async def fake_generate_cv_content(**kwargs):
        return "AI tarafından üretilmiş CV içeriği."

    monkeypatch.setattr("backend.ai.gemini_client.generate_cv_content", fake_generate_cv_content)

    res = client.post(
        "/api/cvs/generate",
        json={"variant_type": "cyber", "skills": ["Python", "Nmap"]},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["variant_type"] == "cyber"
    assert body["is_ai_generated"] is True
    assert body["extracted_text"] == "AI tarafından üretilmiş CV içeriği."


def test_generate_cv_merges_linkedin_data_into_experience(client, monkeypatch):
    headers = _auth_headers(client, "cv-gen-linkedin@example.com")
    client.patch("/api/users/profile", json={"linkedin_data": "Deneyim:\nX Şirketi - Stajyer"}, headers=headers)

    captured = {}

    async def fake_generate_cv_content(**kwargs):
        captured.update(kwargs)
        return "İçerik"

    monkeypatch.setattr("backend.ai.gemini_client.generate_cv_content", fake_generate_cv_content)

    res = client.post(
        "/api/cvs/generate",
        json={"variant_type": "general", "skills": ["Python"], "experience": "Kendi yazdığım deneyim."},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    assert "Kendi yazdığım deneyim." in captured["experience"]
    assert "X Şirketi - Stajyer" in captured["experience"]


def test_generate_cv_merges_structured_experience_and_certificates(client, monkeypatch):
    headers = _auth_headers(client, "cv-gen-structured@example.com")
    client.patch(
        "/api/users/profile",
        json={
            "work_experiences": [
                {"title": "Yazılım Stajyeri", "company": "Acme A.Ş.", "start_date": "2025-06", "end_date": "2025-08", "current": False, "description": "API geliştirme."},
            ],
            "certificates": [
                {"name": "AWS Cloud Practitioner", "issuer": "Amazon", "date": "2025-03"},
            ],
        },
        headers=headers,
    )

    captured = {}

    async def fake_generate_cv_content(**kwargs):
        captured.update(kwargs)
        return "İçerik"

    monkeypatch.setattr("backend.ai.gemini_client.generate_cv_content", fake_generate_cv_content)

    res = client.post(
        "/api/cvs/generate",
        json={"variant_type": "general", "skills": ["Python"], "experience": "Kendi yazdığım deneyim."},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    assert "Acme A.Ş." in captured["experience"]
    assert "AWS Cloud Practitioner" in captured["experience"]


def test_delete_cv_removes_it(client, db_session):
    headers = _auth_headers(client, "cv-del@example.com")
    cv = _seed_cv(db_session, "cv-del@example.com")

    res = client.delete(f"/api/cvs/{cv.id}", headers=headers)
    assert res.status_code == 200

    remaining = client.get("/api/cvs/", headers=headers).json()
    assert remaining == []


def test_delete_other_users_cv_returns_404(client, db_session):
    headers_owner = _auth_headers(client, "cv-del-owner@example.com")
    headers_other = _auth_headers(client, "cv-del-other@example.com")
    cv = _seed_cv(db_session, "cv-del-owner@example.com")

    res = client.delete(f"/api/cvs/{cv.id}", headers=headers_other)
    assert res.status_code == 404

    still_there = client.get("/api/cvs/", headers=headers_owner).json()
    assert len(still_there) == 1


def test_set_default_cv_unsets_previous_default(client, db_session):
    headers = _auth_headers(client, "cv-default@example.com")
    cv1 = _seed_cv(db_session, "cv-default@example.com", title="Birinci")
    cv1.is_default = True
    db_session.commit()
    cv2 = _seed_cv(db_session, "cv-default@example.com", title="İkinci")

    res = client.patch(f"/api/cvs/{cv2.id}/set-default", headers=headers)
    assert res.status_code == 200

    cvs = {c["title"]: c for c in client.get("/api/cvs/", headers=headers).json()}
    assert cvs["Birinci"]["is_default"] is False
    assert cvs["İkinci"]["is_default"] is True


def test_upload_rejects_non_pdf_extension(client):
    headers = _auth_headers(client, "cv-upload-bad@example.com")
    res = client.post(
        "/api/cvs/upload",
        data={"title": "Deneme", "variant_type": "general"},
        files={"file": ("cv.txt", b"sadece metin", "text/plain")},
        headers=headers,
    )
    assert res.status_code == 400


def test_upload_pdf_saves_and_extracts_text(client, db_session, monkeypatch):
    headers = _auth_headers(client, "cv-upload-ok@example.com")

    def fake_extract_pdf_text_sync(file_path):
        return "Kısa metin"  # <=50 karakter, arka plan ATS analizi tetiklenmesin

    monkeypatch.setattr("backend.routers.cv.extract_pdf_text_sync", fake_extract_pdf_text_sync)

    res = client.post(
        "/api/cvs/upload",
        data={"title": "Yüklenen CV", "variant_type": "it"},
        files={"file": ("cv.pdf", b"%PDF-1.4 sahte icerik", "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 202, res.text

    cvs = client.get("/api/cvs/", headers=headers).json()
    assert len(cvs) == 1
    assert cvs[0]["title"] == "Yüklenen CV"
    assert cvs[0]["extracted_text"] == "Kısa metin"
    assert cvs[0]["is_ai_generated"] is False


def test_ats_analyze_requires_extracted_text(client, db_session):
    headers = _auth_headers(client, "cv-ats-empty@example.com")
    cv = _seed_cv(db_session, "cv-ats-empty@example.com", extracted_text=None)

    res = client.post(f"/api/cvs/{cv.id}/ats-analyze", headers=headers)
    assert res.status_code == 400


def test_ats_analyze_updates_score_via_background_task(client, db_session, db_engine, monkeypatch):
    import backend.routers.cv as cv_module

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr(cv_module, "SessionLocal", TestSessionLocal)

    async def fake_analyze_cv_ats(cv_text, api_key=None):
        return {
            "score": 82,
            "feedback": "Genel olarak iyi, anahtar kelimeler eklenmeli.",
            "strengths": ["Python"],
            "weaknesses": ["Bulut deneyimi az"],
            "keywords": ["Docker", "AWS"],
        }

    monkeypatch.setattr("backend.ai.gemini_client.analyze_cv_ats", fake_analyze_cv_ats)

    headers = _auth_headers(client, "cv-ats@example.com")
    cv = _seed_cv(db_session, "cv-ats@example.com", extracted_text="A" * 100)

    res = client.post(f"/api/cvs/{cv.id}/ats-analyze", headers=headers)
    assert res.status_code == 202

    updated = client.get(f"/api/cvs/{cv.id}", headers=headers).json()
    assert updated["ats_score"] == 82
    assert updated["strengths"] == ["Python"]
    assert updated["target_keywords"] == ["Docker", "AWS"]
