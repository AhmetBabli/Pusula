"""
Etkinlikler (events router) testleri.

Etkinlik KATALOĞU (başlık/açıklama/tarih vb.) kullanıcılar arasında
paylaşılır, ama DURUM (interested/registered/...) artık EventUserState ile
kullanıcıya özel (audit item #12 — JobUserState'in Job için çözdüğü sınıf
hatanın aynısı Event.status için de vardı: herhangi bir kullanıcının PATCH'i
herkesin durumunu eziyordu).
"""
from backend.tests.conftest import register_and_login


def _auth_headers(client, email="eventtest@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def _create_event(client, headers, **overrides):
    # source_url alanı DB'de unique — varsayılan "" iki elle-eklenen etkinlikte
    # çakışır, bu yüzden başlığa göre benzersiz bir değer üretiyoruz.
    title = overrides.get("title", "Kariyer Günleri")
    payload = {
        "title": title,
        "event_type": "career_fair",
        "location": "İstanbul",
        "is_online": False,
        "is_free": True,
        "source_url": f"https://example.com/etkinlik/{title}",
        **overrides,
    }
    return client.post("/api/events/", json=payload, headers=headers)


def test_create_and_get_event(client):
    headers = _auth_headers(client)
    res = _create_event(client, headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["title"] == "Kariyer Günleri"
    assert body["status"] == "found"  # model varsayılanı

    detail = client.get(f"/api/events/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == body["id"]


def test_get_missing_event_404(client):
    headers = _auth_headers(client)
    res = client.get("/api/events/999999", headers=headers)
    assert res.status_code == 404


def test_list_events_filters_by_type_and_status(client):
    headers = _auth_headers(client)
    _create_event(client, headers, title="Hackathon", event_type="hackathon")
    _create_event(client, headers, title="Networking Akşamı", event_type="networking")

    hackathons = client.get("/api/events/", params={"event_type": "hackathon"}, headers=headers).json()
    titles = [e["title"] for e in hackathons]
    assert "Hackathon" in titles
    assert "Networking Akşamı" not in titles


def test_update_event_status_valid(client):
    headers = _auth_headers(client)
    event = _create_event(client, headers).json()

    res = client.patch(f"/api/events/{event['id']}/status", json={"status": "registered"}, headers=headers)
    assert res.status_code == 200

    updated = client.get(f"/api/events/{event['id']}", headers=headers).json()
    assert updated["status"] == "registered"


def test_update_event_status_rejects_invalid_value(client):
    headers = _auth_headers(client)
    event = _create_event(client, headers).json()

    res = client.patch(f"/api/events/{event['id']}/status", json={"status": "cok_alakasiz_bir_durum"}, headers=headers)
    assert res.status_code == 400


def test_event_status_is_isolated_per_user(client):
    """Regresyon testi: iki kullanıcı aynı etkinliği farklı durumlara
    işaretleyebilmeli, biri diğerini ezmemeli (audit item #12)."""
    headers_a = _auth_headers(client, "event-user-a@example.com")
    headers_b = _auth_headers(client, "event-user-b@example.com")

    event = _create_event(client, headers_a).json()

    client.patch(f"/api/events/{event['id']}/status", json={"status": "registered"}, headers=headers_a)
    client.patch(f"/api/events/{event['id']}/status", json={"status": "skipped"}, headers=headers_b)

    view_a = client.get(f"/api/events/{event['id']}", headers=headers_a).json()
    view_b = client.get(f"/api/events/{event['id']}", headers=headers_b).json()
    assert view_a["status"] == "registered"
    assert view_b["status"] == "skipped"
