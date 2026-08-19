"""
OutreachAgent'ın alan adı doğrulama mantığı testleri.

hunt_email_with_source, Gemini'nin bulduğu e-postanın alan adının, yine
Gemini'nin "resmi site" dediği source_url'in alan adıyla örtüşüp
örtüşmediğini kontrol eder — örtüşmüyorsa (muhtemelen alakasız bir
e-posta/site birleşimi halüsinasyonu) sonucu reddeder. Gerçek Gemini
çağrısı burada hiç yapılmaz — client mock'lanır.
"""
import json
import pytest
from backend.automation.outreach_agent import OutreachAgent


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, text):
        self._text = text

    async def generate_content(self, **kwargs):
        return _FakeResponse(self._text)


class _FakeAio:
    def __init__(self, text):
        self.models = _FakeModels(text)


class _FakeClient:
    def __init__(self, text):
        self.aio = _FakeAio(text)


def _mock_gemini_response(monkeypatch, email, source_url):
    payload = json.dumps({"email": email, "source_url": source_url})

    def fake_client_ctor(api_key=None):
        return _FakeClient(payload)

    monkeypatch.setattr("backend.automation.outreach_agent.genai.Client", fake_client_ctor)


@pytest.mark.parametrize("domain_or_url,expected", [
    ("sirket.com.tr", "sirket"),
    ("https://www.sirket.com.tr/kariyer", "sirket"),
    ("mail.sirket.com", "sirket"),
    ("https://sirket.com", "sirket"),
])
def test_domain_core_extracts_meaningful_name(domain_or_url, expected):
    assert OutreachAgent._domain_core(domain_or_url) == expected


@pytest.mark.asyncio
async def test_hunt_email_accepts_matching_domain(monkeypatch):
    _mock_gemini_response(monkeypatch, "ik@sirket.com.tr", "https://www.sirket.com.tr/kariyer")
    email, source_url = await OutreachAgent.hunt_email_with_source("Sirket A.Ş.", api_key="fake-key")
    assert email == "ik@sirket.com.tr"
    assert source_url == "https://www.sirket.com.tr/kariyer"


@pytest.mark.asyncio
async def test_hunt_email_rejects_mismatched_domain(monkeypatch):
    """Gemini alakasız bir e-posta + site birleşimi halüsinasyon yaparsa
    (ör. e-posta 'baska-sirket.com'dan ama site 'sirket.com.tr'), reddedilmeli."""
    _mock_gemini_response(monkeypatch, "ik@baska-sirket.com", "https://www.sirket.com.tr/kariyer")
    email, source_url = await OutreachAgent.hunt_email_with_source("Sirket A.Ş.", api_key="fake-key")
    assert email == ""
    assert source_url == ""


@pytest.mark.asyncio
async def test_hunt_email_wrapper_still_returns_plain_string(monkeypatch):
    """Geriye uyumluluk: hunt_email (routers/outreach.py'nin kullandığı) hâlâ
    düz bir string döner, tuple değil."""
    _mock_gemini_response(monkeypatch, "ik@sirket.com", "https://sirket.com")
    email = await OutreachAgent.hunt_email("Sirket A.Ş.", api_key="fake-key")
    assert email == "ik@sirket.com"
