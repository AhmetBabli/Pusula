"""
Mülakat Simülatörü ve Araştırma Asistanı'nın Gemini 503 ("high demand")
yanıtlarına karşı davranışı.

Önceki hâl: bu iki modül kendi ham genai.Client çağrılarını yapıyor ve
HERHANGİ bir hatayı sessizce yutup ya sahte bir tek-soru mülakat ya da
"0 sonuç bulundu" gibi YANLIŞLIKLA BAŞARILI görünen bir sonuç döndürüyordu
— kullanıcı Gemini'nin o an gerçekten çökük olduğunu hiç göremiyordu
(İletişim Asistanı'nın zaten doğru yaptığı gibi "Başarısız" göstermek
yerine). Artık ikisi de gemini_client.py::_call_model_async_json ile aynı
disiplini paylaşıyor: geçici ServerError'da kısa aralıklarla 2 kez daha
dener, hâlâ başarısızsa AIServiceError fırlatır.
"""
import json
import pytest
from google.genai import errors as genai_errors

from backend.exceptions import AIServiceError
from backend.ai.interview_coach_agent import generate_questions, evaluate_answer
from backend.ai.web_search_agent import search_jobs_live


async def _no_sleep(*args, **kwargs):
    return None


def _server_error():
    return genai_errors.ServerError(503, {"error": {"message": "high demand"}}, None)


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FlakyThenSuccessModels:
    """İlk N çağrıda ServerError fırlatır, sonra başarılı yanıt döner."""

    def __init__(self, fail_times, success_text):
        self.fail_times = fail_times
        self.success_text = success_text
        self.calls = 0

    async def generate_content(self, **kwargs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise _server_error()
        return _FakeResponse(self.success_text)


class _AlwaysFailModels:
    def __init__(self):
        self.calls = 0

    async def generate_content(self, **kwargs):
        self.calls += 1
        raise _server_error()


class _FakeAio:
    def __init__(self, models):
        self.models = models


class _FakeClient:
    def __init__(self, models):
        self.aio = _FakeAio(models)


def _patch_genai_client(monkeypatch, module_path, models):
    monkeypatch.setattr(f"{module_path}.genai.Client", lambda api_key=None: _FakeClient(models))
    return models


@pytest.mark.asyncio
async def test_generate_questions_retries_and_recovers_from_transient_503(monkeypatch):
    success_text = json.dumps([
        {"id": 1, "question": "Kendinizi tanıtır mısınız?", "type": "hr", "hint": "..."},
        {"id": 2, "question": "Python deneyiminiz nedir?", "type": "technical", "hint": "..."},
    ])
    models = _FlakyThenSuccessModels(fail_times=2, success_text=success_text)
    _patch_genai_client(monkeypatch, "backend.ai.interview_coach_agent", models)
    monkeypatch.setattr("backend.ai.interview_coach_agent.asyncio.sleep", _no_sleep)

    questions = await generate_questions(
        job_title="Staj", job_description="", company_name="Test A.Ş.", count=5,
    )
    assert len(questions) == 2
    assert models.calls == 3


@pytest.mark.asyncio
async def test_generate_questions_raises_ai_service_error_after_exhausting_retries(monkeypatch):
    models = _AlwaysFailModels()
    _patch_genai_client(monkeypatch, "backend.ai.interview_coach_agent", models)
    monkeypatch.setattr("backend.ai.interview_coach_agent.asyncio.sleep", _no_sleep)

    with pytest.raises(AIServiceError):
        await generate_questions(job_title="Staj", job_description="", company_name="Test A.Ş.", count=5)
    assert models.calls == 3  # ilk deneme + 2 tekrar


@pytest.mark.asyncio
async def test_evaluate_answer_raises_ai_service_error_instead_of_fake_score(monkeypatch):
    models = _AlwaysFailModels()
    _patch_genai_client(monkeypatch, "backend.ai.interview_coach_agent", models)
    monkeypatch.setattr("backend.ai.interview_coach_agent.asyncio.sleep", _no_sleep)

    with pytest.raises(AIServiceError):
        await evaluate_answer(
            question="Soru", answer="Cevap", question_type="hr", hint="",
            job_title="Staj", company_name="Test A.Ş.",
        )


@pytest.mark.asyncio
async def test_search_jobs_live_raises_ai_service_error_after_exhausting_retries(monkeypatch):
    models = _AlwaysFailModels()
    _patch_genai_client(monkeypatch, "backend.ai.web_search_agent", models)
    monkeypatch.setattr("backend.ai.web_search_agent.asyncio.sleep", _no_sleep)

    with pytest.raises(AIServiceError):
        await search_jobs_live("İstanbul React Staj")
    assert models.calls == 3


@pytest.mark.asyncio
async def test_search_jobs_live_returns_parsed_jobs_on_success(monkeypatch):
    success_text = 'Bulduğum ilanlar: [{"title": "React Stajyeri", "company": "Test A.Ş.", "location": "İstanbul", "source_url": "https://x.com/1", "description": "...", "job_type": "staj"}]'
    models = _FlakyThenSuccessModels(fail_times=0, success_text=success_text)
    _patch_genai_client(monkeypatch, "backend.ai.web_search_agent", models)

    jobs = await search_jobs_live("İstanbul React Staj")
    assert len(jobs) == 1
    assert jobs[0]["title"] == "React Stajyeri"
    assert jobs[0]["source"] == "gemini_grounding"
