"""
🧹 Database Maintenance Scripts
Cleanup orphan records, validate constraints, etc.
"""
import logging
from sqlalchemy import text
from backend.database import SessionLocal
from backend.config import settings

logger = logging.getLogger("KariyerAjani.Maintenance")


def cleanup_orphan_records():
    """Clean up orphan records in database"""
    db = SessionLocal()
    
    try:
        # Cleanup orphan CVs (CVs with deleted users)
        orphan_cvs = db.execute(
            text("""
                DELETE FROM cvs 
                WHERE user_id NOT IN (SELECT id FROM user_profiles)
            """)
        )
        logger.info(f"Deleted {orphan_cvs.rowcount} orphan CV records")
        
        # Cleanup orphan Applications (Applications with deleted jobs/CVs)
        orphan_apps = db.execute(
            text("""
                DELETE FROM applications 
                WHERE job_id NOT IN (SELECT id FROM jobs) 
                   OR cv_id IS NOT NULL AND cv_id NOT IN (SELECT id FROM cvs)
            """)
        )
        logger.info(f"Deleted {orphan_apps.rowcount} orphan Application records")
        
        db.commit()
        logger.info("Database cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_constraints():
    """Verify database constraints"""
    db = SessionLocal()
    
    try:
        # Count orphan CVs
        orphan_cv_count = db.execute(
            text("""
                SELECT COUNT(*) as count FROM cvs 
                WHERE user_id NOT IN (SELECT id FROM user_profiles)
            """)
        ).scalar()
        
        if orphan_cv_count > 0:
            logger.warning(f"⚠️ Found {orphan_cv_count} orphan CV records")
        
        # Count orphan Applications
        orphan_app_count = db.execute(
            text("""
                SELECT COUNT(*) as count FROM applications 
                WHERE job_id NOT IN (SELECT id FROM jobs)
            """)
        ).scalar()
        
        if orphan_app_count > 0:
            logger.warning(f"⚠️ Found {orphan_app_count} orphan Application records")
        
        logger.info("✅ Constraint verification completed")
        
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧹 Database Maintenance")
    print("=" * 50)
    
    print("\n1. Verifying constraints...")
    verify_constraints()
    
    print("\n2. Cleaning up orphan records...")
    cleanup_orphan_records()
    
    print("\n✅ Maintenance complete!")
