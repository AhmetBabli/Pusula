"""
POST /agents/outreach/sync (senkron cold email + LinkedIn DM taslağı) testleri.

Bu uç eskiden gemini_client.py'nin geri kalanından bağımsız, retry/timeout/
hata yönetimi olmayan iki AYRI ham Gemini çağrısı yapıyordu — model boş yanıt
döndürdüğünde (güvenlik bloğu) `.text.strip()` doğrudan AttributeError ile
500 veriyordu. Artık _run_outreach ile aynı yardımcıyı (_call_model_async_json)
kullanıyor (audit item #16).
"""
from backend.tests.conftest import register_and_login
from backend.exceptions import AIServiceError


def _auth_headers(client, email="outreachsync@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def test_outreach_sync_returns_combined_drafts(client, monkeypatch):
    headers = _auth_headers(client)

    async def fake_call_model_async_json(prompt, timeout_seconds=30, api_key=None):
        return {"cold_email": "Sayın İlgili, ...", "linkedin_dm": "Merhaba, ..."}

    monkeypatch.setattr("backend.ai.gemini_client._call_model_async_json", fake_call_model_async_json)

    res = client.post(
        "/api/agents/outreach/sync",
        json={"session_id": "s1", "company_name": "Test A.Ş.", "job_title": "Yazılım Stajyeri", "job_description": "Python bilgisi aranıyor."},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cold_email"] == "Sayın İlgili, ..."
    assert body["linkedin_dm"] == "Merhaba, ..."


def test_outreach_sync_surfaces_ai_failure_instead_of_crashing(client, monkeypatch):
    """Regresyon testi: model boş/güvenlik-bloklu yanıt döndürdüğünde eskiden
    ham .text erişimi AttributeError ile 500 veriyordu. Artık temiz bir 503
    dönmeli (AIServiceError -> global exception handler)."""
    headers = _auth_headers(client)

    async def fake_call_model_async_json_fails(prompt, timeout_seconds=30, api_key=None):
        raise AIServiceError("Gemini modelinden boş yanıt döndü.")

    monkeypatch.setattr("backend.ai.gemini_client._call_model_async_json", fake_call_model_async_json_fails)

    res = client.post(
        "/api/agents/outreach/sync",
        json={"session_id": "s1", "company_name": "Test A.Ş.", "job_title": "Yazılım Stajyeri", "job_description": "Python bilgisi aranıyor."},
        headers=headers,
    )
    assert res.status_code == 503
