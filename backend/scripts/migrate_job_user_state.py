"""
Tek seferlik migration: status/is_favorite/match_score/match_explanation/
best_cv_id/missing_skills sütunlarını paylaşılan Job tablosundan kullanıcı
bazlı JobUserState tablosuna taşır (Alembic yok, elle çalıştırılır).

Çalıştırma: python -m backend.scripts.migrate_job_user_state
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
from backend.models.job_user_state import JobUserState
from backend.models.user import UserProfile
from backend.models.cv import CV


def backup_db():
    db_path = PROJECT_ROOT / "kariyer_ajani.db"
    if not db_path.exists():
        print(f"[!] {db_path} bulunamadı, backup atlanıyor (muhtemelen farklı bir DB kullanılıyor).")
        return
    backup_path = db_path.with_suffix(".db.bak")
    shutil.copy2(db_path, backup_path)
    print(f"[+] Yedek alındı: {backup_path}")


def column_exists(conn, table, column) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def migrate():
    backup_db()

    with engine.connect() as conn:
        if not column_exists(conn, "jobs", "status"):
            print("[i] 'status' sütunu jobs tablosunda yok — migration zaten uygulanmış görünüyor, çıkılıyor.")
            return

    # 1) job_user_states tablosunu oluştur
    JobUserState.__table__.create(bind=engine, checkfirst=True)
    print("[+] job_user_states tablosu oluşturuldu (veya zaten vardı).")

    # 2) Backfill: mevcut Job satırlarındaki durumu JobUserState'e taşı
    db = SessionLocal()
    try:
        fallback_user = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
        rows = db.execute(text(
            "SELECT id, status, is_favorite, match_score, match_explanation, best_cv_id, missing_skills "
            "FROM jobs"
        )).fetchall()

        migrated = 0
        skipped_no_user = 0
        now = datetime.now(timezone.utc)

        for job_id, status, is_favorite, match_score, match_explanation, best_cv_id, missing_skills in rows:
            is_default_state = (
                (status is None or status == "new")
                and not is_favorite
                and (match_score is None or match_score == 0)
                and best_cv_id is None
            )
            if is_default_state:
                continue  # Hiç etkileşilmemiş ilan — taşınacak anlamlı bir durum yok

            owner_id = None
            if best_cv_id is not None:
                cv = db.query(CV).filter(CV.id == best_cv_id).first()
                if cv:
                    owner_id = cv.user_id
            if owner_id is None and fallback_user:
                owner_id = fallback_user.id

            if owner_id is None:
                skipped_no_user += 1
                continue

            existing = db.query(JobUserState).filter(
                JobUserState.user_id == owner_id, JobUserState.job_id == job_id
            ).first()
            if existing:
                continue

            db.add(JobUserState(
                user_id=owner_id,
                job_id=job_id,
                status=status or "new",
                is_favorite=bool(is_favorite),
                match_score=match_score or 0.0,
                match_explanation=match_explanation,
                best_cv_id=best_cv_id,
                missing_skills=missing_skills,
                created_at=now,
                updated_at=now,
            ))
            migrated += 1

        db.commit()
        print(f"[+] {migrated} JobUserState satırı oluşturuldu (backfill). Atlanan (sahipsiz): {skipped_no_user}.")
    finally:
        db.close()

    # 3) Eski sütunları jobs tablosundan kaldır (SQLite 3.35+ DROP COLUMN destekliyor)
    old_columns = ["match_score", "match_explanation", "best_cv_id", "missing_skills", "status", "is_favorite"]
    with engine.begin() as conn:
        for col in old_columns:
            if column_exists(conn, "jobs", col):
                conn.execute(text(f"ALTER TABLE jobs DROP COLUMN {col}"))
                print(f"[+] jobs.{col} kaldırıldı.")

    print("[OK] Migration tamamlandı.")


if __name__ == "__main__":
    migrate()
