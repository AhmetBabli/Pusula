"""
Gelen kutusu (inbox router) testleri: hesap bağlama, kullanıcı izolasyonu ve
arka planda çalışan e-posta senkronizasyonu.

run_sync_background kendi SessionLocal()'ını açtığı için (Depends(get_db)
override'ından etkilenmez) — test'in izole in-memory motoruna monkeypatch ile
yönlendiriliyor, gerçek dev DB'ye asla dokunmuyor (bkz.
test_jobs.py::test_run_job_sync_matches_per_user, test_cv.py'deki aynı desen).
"""
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from backend.tests.conftest import register_and_login
from backend.models.user import UserProfile
from backend.models.inbox import EmailAccount, InboxItem


def _auth_headers(client, email="inboxtest@example.com"):
    token = register_and_login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


def _seed_account(db_session, email, account_email="mail@gmail.com"):
    user = db_session.query(UserProfile).filter(UserProfile.email == email).first()
    account = EmailAccount(user_id=user.id, email=account_email)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


def test_add_account_creates_new_and_hides_password(client):
    headers = _auth_headers(client, "inbox-add@example.com")
    res = client.post(
        "/api/inbox/accounts",
        json={"email": "add-test@gmail.com", "app_password": "gizli-sifre"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["email"] == "add-test@gmail.com"
    assert body["is_active"] is True
    assert "app_password" not in body


def test_add_account_updates_existing_for_same_user(client, db_session):
    headers = _auth_headers(client, "inbox-update@example.com")
    account = _seed_account(db_session, "inbox-update@example.com", account_email="existing@gmail.com")
    account.is_active = False
    db_session.commit()

    res = client.post(
        "/api/inbox/accounts",
        json={"email": "existing@gmail.com", "app_password": "yeni-sifre"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is True


def test_add_account_conflicts_when_owned_by_another_user(client, db_session):
    headers_a = _auth_headers(client, "inbox-owner@example.com")
    headers_b = _auth_headers(client, "inbox-intruder@example.com")
    _seed_account(db_session, "inbox-owner@example.com", account_email="taken@gmail.com")

    res = client.post(
        "/api/inbox/accounts",
        json={"email": "taken@gmail.com", "app_password": "xxx"},
        headers=headers_b,
    )
    assert res.status_code == 400


def test_get_accounts_only_returns_own(client, db_session):
    headers_a = _auth_headers(client, "inbox-list-a@example.com")
    headers_b = _auth_headers(client, "inbox-list-b@example.com")
    _seed_account(db_session, "inbox-list-a@example.com", account_email="a@gmail.com")
    _seed_account(db_session, "inbox-list-b@example.com", account_email="b@gmail.com")

    list_a = client.get("/api/inbox/accounts", headers=headers_a).json()
    list_b = client.get("/api/inbox/accounts", headers=headers_b).json()

    assert [a["email"] for a in list_a] == ["a@gmail.com"]
    assert [a["email"] for a in list_b] == ["b@gmail.com"]


def test_get_inbox_items_only_returns_own(client, db_session):
    headers_a = _auth_headers(client, "inbox-items-a@example.com")
    headers_b = _auth_headers(client, "inbox-items-b@example.com")
    account_a = _seed_account(db_session, "inbox-items-a@example.com", account_email="items-a@gmail.com")

    item = InboxItem(
        account_id=account_a.id,
        uid="uid-1",
        item_type="job",
        title="Yazılım Stajyeri İlanı",
        sender="ik@sirket.com",
        body_summary="Kısa özet",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.commit()

    items_a = client.get("/api/inbox/items", headers=headers_a).json()
    items_b = client.get("/api/inbox/items", headers=headers_b).json()

    assert len(items_a) == 1
    assert items_a[0]["title"] == "Yazılım Stajyeri İlanı"
    assert items_b == []


def test_mark_item_read_updates_flag(client, db_session):
    headers = _auth_headers(client, "inbox-read@example.com")
    account = _seed_account(db_session, "inbox-read@example.com", account_email="read@gmail.com")
    item = InboxItem(
        account_id=account.id,
        uid="uid-read",
        item_type="job",
        title="Okunmamış İlan",
        sender="ik@sirket.com",
        body_summary="Özet",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    res = client.patch(f"/api/inbox/items/{item.id}/read", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_read"] is True


def test_mark_item_read_404_for_other_users_item(client, db_session):
    headers_owner = _auth_headers(client, "inbox-read-owner@example.com")
    headers_other = _auth_headers(client, "inbox-read-other@example.com")
    account = _seed_account(db_session, "inbox-read-owner@example.com", account_email="read-owner@gmail.com")
    item = InboxItem(
        account_id=account.id, uid="uid-read2", item_type="job", title="Başkasının Öğesi",
        sender="ik@sirket.com", body_summary="", received_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    res = client.patch(f"/api/inbox/items/{item.id}/read", headers=headers_other)
    assert res.status_code == 404


def test_convert_job_item_creates_job_and_marks_applied(client, db_session):
    from backend.models.job import Job

    headers = _auth_headers(client, "inbox-convert@example.com")
    account = _seed_account(db_session, "inbox-convert@example.com", account_email="convert@gmail.com")
    item = InboxItem(
        account_id=account.id,
        uid="uid-convert",
        item_type="job",
        title="Veri Analisti Stajyeri",
        sender="İnsan Kaynakları <ik@ornek-sirket.com>",
        body_summary="Kısa özet",
        content_original="Tam e-posta metni burada.",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    res = client.post(f"/api/inbox/items/{item.id}/convert-to-job", headers=headers)
    assert res.status_code == 200, res.text
    job_id = res.json()["job_id"]

    job = db_session.query(Job).filter(Job.id == job_id).first()
    assert job is not None
    assert job.title == "Veri Analisti Stajyeri"
    assert job.company == "İnsan Kaynakları"
    assert job.description == "Tam e-posta metni burada."
    assert job.source_url == f"inbox://item/{item.id}"

    db_session.refresh(item)
    assert item.is_applied is True


def test_convert_non_job_item_rejected(client, db_session):
    headers = _auth_headers(client, "inbox-convert-bad@example.com")
    account = _seed_account(db_session, "inbox-convert-bad@example.com", account_email="convert-bad@gmail.com")
    item = InboxItem(
        account_id=account.id, uid="uid-convert-bad", item_type="event", title="Bir Etkinlik",
        sender="etkinlik@ornek.com", body_summary="", received_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    res = client.post(f"/api/inbox/items/{item.id}/convert-to-job", headers=headers)
    assert res.status_code == 400


def test_sync_requires_linked_account(client):
    headers = _auth_headers(client, "inbox-sync-none@example.com")
    res = client.post("/api/inbox/sync", headers=headers)
    assert res.status_code == 400


def test_sync_fetches_and_stores_new_items(client, db_session, db_engine, monkeypatch):
    import backend.routers.inbox as inbox_module

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr(inbox_module, "SessionLocal", TestSessionLocal)

    headers = _auth_headers(client, "inbox-sync-ok@example.com")
    account = _seed_account(db_session, "inbox-sync-ok@example.com", account_email="sync-ok@gmail.com")

    fake_email = {
        "uid": "uid-42",
        "subject": "Mülakat Daveti",
        "sender": "ik@sirket.com",
        "body": "Yarın saat 14:00'te görüşelim.",
        "received_at": datetime.now(timezone.utc),
    }

    monkeypatch.setattr("backend.automation.gmail_service.GmailService.connect", lambda self: True)
    monkeypatch.setattr(
        "backend.automation.gmail_service.GmailService.fetch_latest_emails",
        lambda self, limit=20: [fake_email],
    )
    monkeypatch.setattr("backend.automation.gmail_service.GmailService.disconnect", lambda self: None)

    async def fake_process_email(subject, sender, body, api_key=None):
        return {"type": "interview", "title": "Mülakat Daveti", "summary": "Yarın mülakat var."}

    monkeypatch.setattr("backend.ai.email_agent.EmailIntelligenceAgent.process_email", fake_process_email)

    res = client.post("/api/inbox/sync", headers=headers)
    assert res.status_code == 202

    items = client.get("/api/inbox/items", headers=headers).json()
    assert len(items) == 1
    assert items[0]["item_type"] == "interview"
    assert items[0]["title"] == "Mülakat Daveti"


def test_sync_skips_already_seen_email(client, db_session, db_engine, monkeypatch):
    import backend.routers.inbox as inbox_module

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr(inbox_module, "SessionLocal", TestSessionLocal)

    headers = _auth_headers(client, "inbox-sync-dup@example.com")
    account = _seed_account(db_session, "inbox-sync-dup@example.com", account_email="sync-dup@gmail.com")
    db_session.add(InboxItem(
        account_id=account.id,
        uid="uid-seen",
        item_type="job",
        title="Zaten görülmüş",
        sender="eski@sirket.com",
        body_summary="",
        received_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    fake_email = {
        "uid": "uid-seen",
        "subject": "Zaten görülmüş",
        "sender": "eski@sirket.com",
        "body": "...",
        "received_at": datetime.now(timezone.utc),
    }

    monkeypatch.setattr("backend.automation.gmail_service.GmailService.connect", lambda self: True)
    monkeypatch.setattr(
        "backend.automation.gmail_service.GmailService.fetch_latest_emails",
        lambda self, limit=20: [fake_email],
    )
    monkeypatch.setattr("backend.automation.gmail_service.GmailService.disconnect", lambda self: None)

    called = {"count": 0}

    async def fake_process_email(subject, sender, body, api_key=None):
        called["count"] += 1
        return {"type": "job", "title": subject, "summary": ""}

    monkeypatch.setattr("backend.ai.email_agent.EmailIntelligenceAgent.process_email", fake_process_email)

    res = client.post("/api/inbox/sync", headers=headers)
    assert res.status_code == 202

    items = client.get("/api/inbox/items", headers=headers).json()
    assert len(items) == 1  # yeni satır eklenmedi, mevcut korundu
    assert called["count"] == 0  # zaten görülen e-posta için AI hiç çağrılmadı
