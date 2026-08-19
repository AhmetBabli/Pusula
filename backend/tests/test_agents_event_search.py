"""
Etkinlik Bulucu (Gemini Grounding ile canlı etkinlik arama) regresyon testleri.

_run_event_search kendi SessionLocal()'ını açıyor — test'in izole in-memory
motoruna monkeypatch ile yönlendiriliyor (bkz. test_jobs.py::test_run_job_sync_
matches_per_user'daki aynı desen), gerçek dev DB'ye asla dokunmuyor.
"""
from sqlalchemy.orm import sessionmaker

from backend.tests.conftest import register_and_login
from backend.models.event import Event


def _auth_headers(client, email="eventsearch@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


async def _run(monkeypatch, db_engine, fake_events, session_id="test-session", user_id=None):
    import backend.routers.agents as agents_module

    # _run_event_search kendi SessionLocal()'ını fonksiyon içinde yerel importla
    # alıyor (from backend.database import SessionLocal) — bu yüzden modül
    # seviyesinde değil, gerçek kaynakta (backend.database) monkeypatch'lenmeli.
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr("backend.database.SessionLocal", TestSessionLocal)

    async def fake_search_events_live(query, location, user_context="", api_key=None):
        return fake_events

    async def fake_push_agent_event(*a, **k):
        return None

    monkeypatch.setattr("backend.ai.web_search_agent.search_events_live", fake_search_events_live)
    monkeypatch.setattr(agents_module, "push_agent_event", fake_push_agent_event)

    await agents_module._run_event_search(session_id, "İstanbul kariyer fuarı", "İstanbul", user_id)


def test_run_event_search_saves_events_with_relevance(client, db_session, db_engine, monkeypatch):
    import asyncio
    from backend.models.user import UserProfile

    headers = _auth_headers(client, "eventsearch-a@example.com")
    user = db_session.query(UserProfile).filter(UserProfile.email == "eventsearch-a@example.com").first()

    fake_events = [
        {
            "title": "İstanbul Kariyer Fuarı 2026",
            "organizer": "Test Organizasyon",
            "description": "Teknoloji şirketlerinin katılacağı fuar.",
            "event_type": "career_fair",
            "location": "İstanbul",
            "is_online": False,
            "is_free": True,
            "event_date": None,
            "source_url": "https://example.com/etkinlik/kariyer-fuari-2026",
            "relevance_score": 82,
            "relevance_reason": "YBS öğrencisi için uygun.",
        }
    ]

    asyncio.run(_run(monkeypatch, db_engine, fake_events, user_id=user.id))

    event = db_session.query(Event).filter(Event.source_url == "https://example.com/etkinlik/kariyer-fuari-2026").first()
    assert event is not None
    assert event.title == "İstanbul Kariyer Fuarı 2026"
    assert event.relevance_score == 82
    assert event.relevance_reason == "YBS öğrencisi için uygun."
    assert event.source == "gemini_grounding"


def test_run_event_search_skips_entries_without_source_url(client, db_session, db_engine, monkeypatch):
    import asyncio
    from backend.models.user import UserProfile

    headers = _auth_headers(client, "eventsearch-b@example.com")
    user = db_session.query(UserProfile).filter(UserProfile.email == "eventsearch-b@example.com").first()

    fake_events = [
        {"title": "Linksiz Etkinlik", "event_type": "seminar", "source_url": "", "relevance_score": 50, "relevance_reason": ""},
    ]

    asyncio.run(_run(monkeypatch, db_engine, fake_events, user_id=user.id))

    assert db_session.query(Event).filter(Event.title == "Linksiz Etkinlik").first() is None


def test_run_event_search_deduplicates_by_source_url(client, db_session, db_engine, monkeypatch):
    import asyncio
    from backend.models.user import UserProfile

    headers = _auth_headers(client, "eventsearch-c@example.com")
    user = db_session.query(UserProfile).filter(UserProfile.email == "eventsearch-c@example.com").first()

    db_session.add(Event(
        title="Zaten Var Olan Etkinlik", source="manual",
        source_url="https://example.com/etkinlik/dup-1", event_type="seminar",
    ))
    db_session.commit()

    fake_events = [
        {"title": "Zaten Var Olan Etkinlik (güncel)", "event_type": "seminar",
         "source_url": "https://example.com/etkinlik/dup-1", "relevance_score": 60, "relevance_reason": ""},
    ]

    asyncio.run(_run(monkeypatch, db_engine, fake_events, user_id=user.id))

    matches = db_session.query(Event).filter(Event.source_url == "https://example.com/etkinlik/dup-1").all()
    assert len(matches) == 1
    assert matches[0].title == "Zaten Var Olan Etkinlik"  # eskisi korunmalı, ezilmemeli
