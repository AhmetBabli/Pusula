"""
Mülakat Koçu sesli okuma (TTS) ucu regresyon testleri.
"""
from backend.tests.conftest import register_and_login


def _auth_headers(client, email="ttstest@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def test_tts_returns_audio_bytes(client, monkeypatch):
    headers = _auth_headers(client)

    async def fake_synthesize_speech(text, language_code="tr-TR"):
        assert text == "Kendinizi tanıtır mısınız?"
        return b"\xff\xfb\x90fake-mp3-bytes"

    monkeypatch.setattr("backend.ai.tts_client.synthesize_speech", fake_synthesize_speech)

    res = client.post("/api/agents/tts", json={"text": "Kendinizi tanıtır mısınız?"}, headers=headers)

    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/mpeg"
    assert res.content == b"\xff\xfb\x90fake-mp3-bytes"


def test_tts_rejects_empty_text(client):
    headers = _auth_headers(client, "ttstest-empty@example.com")
    res = client.post("/api/agents/tts", json={"text": ""}, headers=headers)
    assert res.status_code == 422


def test_tts_surfaces_service_error(client, monkeypatch):
    from backend.exceptions import AIServiceError

    headers = _auth_headers(client, "ttstest-error@example.com")

    async def fake_synthesize_speech_fail(text, language_code="tr-TR"):
        raise AIServiceError("Sesli okuma servisi hata döndürdü (500).")

    monkeypatch.setattr("backend.ai.tts_client.synthesize_speech", fake_synthesize_speech_fail)

    res = client.post("/api/agents/tts", json={"text": "test"}, headers=headers)
    assert res.status_code == 503


def test_tts_requires_authentication(client):
    res = client.post("/api/agents/tts", json={"text": "test"})
    assert res.status_code == 401
