"""
Tek seferlik migration: status sütununu paylaşılan Event tablosundan
kullanıcı bazlı EventUserState tablosuna taşır (Alembic yok, elle çalıştırılır).

Job'ın aksine bir etkinliğin "sahibi" kavramı yok (JobUserState migration'ı
best_cv_id üzerinden bir sahip belirleyebiliyordu) — bu yüzden her etkinliğin
mevcut paylaşılan durumu, o anda var olan HER kullanıcı için aynı başlangıç
değeriyle kopyalanır (kimsenin durumu sessizce "found"a sıfırlanmasın diye).

Çalıştırma: python -m backend.scripts.migrate_event_user_state
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from backend.database import engine, SessionLocal
from backend.models.event_user_state import EventUserState
from backend.models.user import UserProfile


def backup_db():
    db_path = PROJECT_ROOT / "kariyer_ajani.db"
    if not db_path.exists():
        print(f"[!] {db_path} bulunamadı, backup atlanıyor (muhtemelen farklı bir DB kullanılıyor).")
        return
    backup_path = db_path.with_suffix(".db.bak_events")
    shutil.copy2(db_path, backup_path)
    print(f"[+] Yedek alındı: {backup_path}")


def column_exists(conn, table, column) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def migrate():
    backup_db()

    with engine.connect() as conn:
        if not column_exists(conn, "events", "status"):
            print("[i] 'status' sütunu events tablosunda yok — migration zaten uygulanmış görünüyor, çıkılıyor.")
            return

    # 1) event_user_states tablosunu oluştur
    EventUserState.__table__.create(bind=engine, checkfirst=True)
    print("[+] event_user_states tablosu oluşturuldu (veya zaten vardı).")

    # 2) Backfill: her etkinliğin mevcut paylaşılan durumunu, o anda var olan
    # her kullanıcı için ayrı bir EventUserState satırına kopyala.
    db = SessionLocal()
    try:
        user_ids = [row[0] for row in db.execute(text("SELECT id FROM user_profiles")).fetchall()]
        events = db.execute(text("SELECT id, status FROM events")).fetchall()

        now = datetime.now(timezone.utc)
        migrated = 0
        for event_id, status in events:
            for user_id in user_ids:
                existing = db.query(EventUserState).filter(
                    EventUserState.user_id == user_id, EventUserState.event_id == event_id
                ).first()
                if existing:
                    continue
                db.add(EventUserState(
                    user_id=user_id,
                    event_id=event_id,
                    status=status or "found",
                    created_at=now,
                    updated_at=now,
                ))
                migrated += 1

        db.commit()
        print(f"[+] {migrated} EventUserState satırı oluşturuldu (backfill: {len(events)} etkinlik x {len(user_ids)} kullanıcı).")
    finally:
        db.close()

    # 3) Eski sütunu events tablosundan kaldır (SQLite 3.35+ DROP COLUMN destekliyor)
    with engine.begin() as conn:
        if column_exists(conn, "events", "status"):
            conn.execute(text("ALTER TABLE events DROP COLUMN status"))
            print("[+] events.status kaldırıldı.")

    print("[OK] Migration tamamlandı.")


if __name__ == "__main__":
    migrate()
