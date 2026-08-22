from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from backend.database import Base
from backend.utils.crypto import encrypt, decrypt

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    # Not: Bu alanlarda bilerek sahte/demo varsayılan değer YOK — SQLAlchemy,
    # Python tarafında `default` verilen bir kolona None atarsan bunu "hiç
    # değer girilmemiş" sayıp default'u sessizce devreye sokar. Yani buraya
    # örn. "Doğuş Üniversitesi" default'u koyarsak, register()/google_auth()
    # `university=None` yazsa bile gerçek kullanıcılara bu sahte veri yazılır
    # (yaşanmış bug). Demo hesabın kendi değerleri seed_data.py'de açıkça set edilir.
    university = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    graduation_year = Column(Integer, nullable=True)

    # 🚀 Modern Yöntem: SQLAlchemy native JSON tipini kullanıyoruz.
    # Artık string çevirileriyle veya json.loads() ile uğraşmaya gerek yok.
    # Doğrudan Python listesi verip liste olarak geri okuyabilirsin.
    target_sectors = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    languages = Column(JSON, default=list)

    linkedin_url = Column(String(300), nullable=True)
    github_url = Column(String(300), nullable=True)
    # LinkedIn'in herkese açık bir API'si yok ve profil kazıması (scraping)
    # kendi kullanım şartlarını ihlal ediyor — bu yüzden kullanıcı kendi
    # profilinden (Deneyim/Eğitim/Beceriler) kopyaladığı ham metni buraya
    # yapıştırıyor. CV üretimi ve kariyer stratejisi bu metni bağlam olarak kullanır.
    linkedin_data = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)  # Kısa biyografi

    # Yapılandırılmış iş deneyimi/sertifika girdileri — CV üretiminde serbest
    # metne çevrilip prompt'a eklenir (bkz. routers/cv.py). Her öğe bir dict:
    # work_experiences: {title, company, start_date, end_date, current, description}
    # certificates: {name, issuer, date}
    work_experiences = Column(JSON, default=list)
    certificates = Column(JSON, default=list)

    # Kullanıcının kendi Gemini API key'i (şifreli) — her kullanıcı kendi
    # kotasını kullansın diye. Boşsa backend'in paylaşılan .env key'ine düşülür.
    _gemini_api_key = Column("gemini_api_key", String(500), nullable=True)

    # Kayıt sonrası bölüm-tanıtımı + bilgi formu tamamlandı mı?
    onboarding_completed = Column(Boolean, default=False, nullable=False)

    # JWT'ler stateless olduğu için tek başına iptal edilemez — bu sayaç
    # token'a "ver" claim'i olarak gömülür. /auth/logout her çağrıldığında
    # artırılır; get_current_user, token'daki değerle burayı karşılaştırıp
    # eşleşmezse reddeder. Böylece "çıkış yap" gerçekten önceki tüm
    # token'ları geçersiz kılar (istemcinin token'ı silmesine güvenmek yerine).
    token_version = Column(Integer, default=0, nullable=False)

    # 🚀 Zaman fonksiyonları güncellendi (Timezone-aware)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Not: get_target_sectors, get_skills gibi manuel JSON parse eden metodlar silindi.
    # Artık sistemin herhangi bir yerinde `user.skills` çağırdığında sana zaten
    # doğrudan ["Python", "SQL", "React"] formatında hazır Python listesi dönecektir.

    @property
    def gemini_api_key(self) -> str:
        return decrypt(self._gemini_api_key) if self._gemini_api_key else ""

    @gemini_api_key.setter
    def gemini_api_key(self, value: str):
        self._gemini_api_key = encrypt(value) if value else None

    @property
    def has_gemini_api_key(self) -> bool:
        return bool(self._gemini_api_key)