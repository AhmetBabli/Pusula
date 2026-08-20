"""
/api/agents/interview/start regresyon testleri: başarı durumunda AI'nin
şirkete özel ürettiği sorular döner (personalized=true); AI servisi geçici
olarak kullanılamadığında (kota/503) mülakat pratiğini tamamen durdurmak
yerine genel yedek sorulara düşer (personalized=false).
"""
from backend.exceptions import AIServiceError
from backend.tests.conftest import register_and_login


def _auth_headers(client, email="interviewstart@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def test_interview_start_returns_personalized_questions_on_success(client, monkeypatch):
    headers = _auth_headers(client)

    async def fake_generate_questions(**kwargs):
        return [{"id": 1, "question": "CV'nizde belirttiğiniz X projesinden bahseder misiniz?", "type": "technical", "hint": "..."}]

    monkeypatch.setattr("backend.ai.interview_coach_agent.generate_questions", fake_generate_questions)

    res = client.post("/api/agents/interview/start", json={
        "session_id": "s1", "company_name": "Trendyol", "job_title": "Yazılım Stajyeri",
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["personalized"] is True
    assert len(data["questions"]) == 1
    assert "X projesinden" in data["questions"][0]["question"]


def test_interview_start_falls_back_when_ai_service_unavailable(client, monkeypatch):
    headers = _auth_headers(client, "interviewstart-fallback@example.com")

    async def fake_generate_questions_fail(**kwargs):
        raise AIServiceError("AI service temporarily unavailable: 429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr("backend.ai.interview_coach_agent.generate_questions", fake_generate_questions_fail)

    res = client.post("/api/agents/interview/start", json={
        "session_id": "s2", "company_name": "Baykar", "job_title": "Gömülü Yazılım Stajyeri",
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["personalized"] is False
    assert len(data["questions"]) > 0
    assert data["total"] == len(data["questions"])


def test_interview_start_fallback_respects_round_type(client, monkeypatch):
    headers = _auth_headers(client, "interviewstart-fallback-hr@example.com")

    async def fake_generate_questions_fail(**kwargs):
        raise AIServiceError("AI service temporarily unavailable")

    monkeypatch.setattr("backend.ai.interview_coach_agent.generate_questions", fake_generate_questions_fail)

    res = client.post("/api/agents/interview/start", json={
        "session_id": "s3", "company_name": "Turkcell", "job_title": "IK Stajyeri", "round_type": "hr",
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["personalized"] is False
    assert all(q["type"] == "hr" for q in data["questions"])
