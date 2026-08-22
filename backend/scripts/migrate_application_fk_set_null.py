"""
Tek seferlik migration: applications.job_id / applications.cv_id sütunlarını
NOT NULL + ON DELETE CASCADE'ten nullable + ON DELETE SET NULL'a çevirir
(Alembic yok, elle çalıştırılır).

SQLite bir foreign key'in ON DELETE davranışını ALTER TABLE ile değiştirmeye
izin vermez — tabloyu (verisiyle birlikte) yeni şemayla yeniden oluşturmak
gerekir.

Çalıştırma: python -m backend.scripts.migrate_application_fk_set_null
"""
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from backend.database import engine
from backend.models.application import Application


def backup_db():
    db_path = PROJECT_ROOT / "kariyer_ajani.db"
    if not db_path.exists():
        print(f"[!] {db_path} bulunamadı, backup atlanıyor (muhtemelen farklı bir DB kullanılıyor).")
        return
    backup_path = db_path.with_suffix(".db.bak_app_fk")
    shutil.copy2(db_path, backup_path)
    print(f"[+] Yedek alındı: {backup_path}")


def already_migrated(conn) -> bool:
    row = conn.execute(text(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='applications'"
    )).fetchone()
    return row is not None and "ON DELETE CASCADE" not in row[0]


def migrate():
    backup_db()

    with engine.connect() as conn:
        if already_migrated(conn):
            print("[i] applications tablosu zaten SET NULL şemasında — migration atlanıyor.")
            return

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(text("ALTER TABLE applications RENAME TO applications_old"))

        # RENAME TABLE, tablonun indekslerini de (aynı isimle) applications_old'a
        # taşır — Application.__table__.create() aşağıda aynı isimlerle yeni
        # indeksler oluşturmaya çalışınca çakışmasın diye önce düşürülüyor.
        index_names = [ix.name for ix in Application.__table__.indexes]
        for name in index_names:
            conn.execute(text(f"DROP INDEX IF EXISTS {name}"))

        Application.__table__.create(bind=conn, checkfirst=False)

        columns = [c.name for c in Application.__table__.columns]
        col_list = ", ".join(columns)
        conn.execute(text(f"INSERT INTO applications ({col_list}) SELECT {col_list} FROM applications_old"))

        moved = conn.execute(text("SELECT COUNT(*) FROM applications")).scalar()
        print(f"[+] {moved} başvuru satırı yeni şemaya taşındı.")

        conn.execute(text("DROP TABLE applications_old"))
        conn.execute(text("PRAGMA foreign_keys=ON"))

    print("[OK] Migration tamamlandı.")


if __name__ == "__main__":
    migrate()
