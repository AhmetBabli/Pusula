"""
Kariyer Ajanı — Seed Data Script
Veritabanına örnek veriler ekler (profil, ilanlar, etkinlikler).
Çalıştırma: python -m backend.seed_data
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import SessionLocal, init_db
from backend.models.user import UserProfile
from backend.models.job import Job
from backend.models.event import Event
from backend.auth import hash_password

SEED_USER_EMAIL = "ahmet@dogus.edu.tr"
SEED_USER_PASSWORD = "kariyer123"  # Sadece geliştirme ortamı için

def seed():
    init_db()
    db = SessionLocal()

    try:
        # ──────────────────────────────────────────
        # 1. Kullanıcı Profili
        # ──────────────────────────────────────────
        if not db.query(UserProfile).filter(UserProfile.email == SEED_USER_EMAIL).first():
            user = UserProfile(
                full_name="Ahmet Babli",
                email=SEED_USER_EMAIL,
                hashed_password=hash_password(SEED_USER_PASSWORD),
                phone="05XX XXX XX XX",
                university="Doğuş Üniversitesi",
                department="Yönetim Bilişim Sistemleri",
                graduation_year=2026,
                target_sectors=["Yapay Zeka", "Siber Güvenlik", "Yazılım Geliştirme", "Veri Analizi"],
                skills=["Python", "Flask", "SQL", "React", "FastAPI", "Docker", "AI API Integration", "Git"],
                languages=["Türkçe", "İngilizce"],
                summary="Yönetim Bilişim Sistemleri öğrencisi. Full-stack geliştirme, yapay zeka entegrasyonları ve veri bilimi alanlarında kariyer hedefliyor.",
                onboarding_completed=True,
            )
            db.add(user)
            print(f"[+] Kullanıcı profili oluşturuldu (email: {SEED_USER_EMAIL}, şifre: {SEED_USER_PASSWORD})")

        # ──────────────────────────────────────────
        # 2. Örnek İş İlanları
        # ──────────────────────────────────────────
        if db.query(Job).count() == 0:
            now_utc = datetime.now(timezone.utc)
            jobs = [
                Job(
                    source="kariyer_net",
                    source_url="https://kariyer.baykartech.com/ornek-1",
                    title="Proje Mühendisi Adayı",
                    company="Baykar Teknoloji",
                    location="İstanbul",
                    job_type="staj",
                    description="Savunma sanayii ve insansız hava araçları projelerinde görev alacak, analitik düşünme yeteneğine sahip proje mühendisi adayı.",
                    requirements="Mühendislik veya YBS öğrencisi, Proje Yönetimi, Python, Analitik Düşünce",
                    sector="Savunma Sanayii / Teknoloji",
                    match_score=88.0,
                    status="new",
                    posted_at=now_utc - timedelta(days=2),
                    deadline=now_utc + timedelta(days=14),
                ),
                Job(
                    source="linkedin",
                    source_url="https://www.linkedin.com/jobs/view/ornek-2",
                    title="İç Denetim ve Bilgi Sistemleri Stajyeri",
                    company="Eczacıbaşı Topluluğu",
                    location="İstanbul (Hibrit)",
                    job_type="staj",
                    description="Bilgi sistemleri denetimi, süreç analizi ve ERP sistemleri üzerinde çalışacak stajyer aranıyor.",
                    requirements="YBS veya Endüstri Mühendisliği, SQL, Süreç Analizi, MS Office",
                    sector="Denetim / IT",
                    match_score=92.0,
                    status="new",
                    posted_at=now_utc - timedelta(days=5),
                    deadline=now_utc + timedelta(days=21),
                ),
                Job(
                    source="youthall",
                    source_url="https://www.youthall.com/tr/firsat/ornek-3",
                    title="Full Stack Developer (Stajyer)",
                    company="Kibar Holding",
                    location="İstanbul",
                    job_type="staj",
                    description="K-Team genç yetenek programı kapsamında, web tabanlı iç uygulamaların geliştirilmesine destek olacak takım arkadaşı.",
                    requirements="Python, React, API Tasarımı, Git, Yenilikçi Düşünce",
                    sector="IT / Bilişim",
                    match_score=85.0,
                    status="new",
                    posted_at=now_utc - timedelta(days=1),
                    deadline=now_utc + timedelta(days=10),
                )
            ]
            db.add_all(jobs)
            print(f"[+] {len(jobs)} örnek iş ilanı eklendi")

        # ──────────────────────────────────────────
        # 3. Örnek Etkinlikler
        # ──────────────────────────────────────────
        if db.query(Event).count() == 0:
            now_utc = datetime.now(timezone.utc)
            events = [
                Event(
                    source="kommunity",
                    source_url="https://kommunity.com/event/ai-workshop",
                    title="Yeni Nesil Yetkinlikler ve Yapay Zeka Entegrasyonları",
                    organizer="Tech Istanbul",
                    description="AI API'lerinin (Gemini, OpenAI) mevcut projelere entegrasyonu ve full-stack mimaride kullanımı.",
                    event_type="workshop",
                    location="Online",
                    is_online=True,
                    is_free=True,
                    event_date=now_utc + timedelta(days=7),
                    registration_deadline=now_utc + timedelta(days=2),
                    relevance_score=95.0,
                    status="found",
                ),
                Event(
                    source="youthall",
                    source_url="https://www.youthall.com/tr/etkinlik/career-fair",
                    title="Doğuş Üniversitesi Kariyer Fuarı 2026",
                    organizer="Doğuş Üniversitesi Kariyer Merkezi",
                    description="Sektörün öncü teknoloji şirketlerinin katılacağı staj ve iş fırsatları fuarı.",
                    event_type="career_fair",
                    location="Doğuş Üniversitesi Kampüsü",
                    is_online=False,
                    is_free=True,
                    event_date=now_utc + timedelta(days=25),
                    registration_deadline=now_utc + timedelta(days=20),
                    relevance_score=100.0,
                    status="found",
                )
            ]
            db.add_all(events)
            print(f"[+] {len(events)} örnek etkinlik eklendi")

        db.commit()
        print("\n[OK] Seed data başarıyla yüklendi!")

    except Exception as e:
        db.rollback()
        print(f"\n[!] HATA: Veritabanına yazılırken bir sorun oluştu! İşlemler geri alındı. Hata detayı:\n{e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()