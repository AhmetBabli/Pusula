# 🏛️ KARİYER AJANI — CTO DENETİM RAPORU
**Denetim Tarihi:** 2025  
**Denetmen:** Kıdemli Yazılım Mimarı & Ürün Stratejisti  
**Proje:** Kariyer Ajanı v1.0.0 (FastAPI + React + Gemini AI)  
**Durum:** `PRE-BETA / GELİŞTİRME AŞAMASI`

---

## 📋 EXECUTIVE SUMMARY

Kariyer Ajanı, **teknik olarak çalışan ama üretime hazır olmayan** bir "MVP+" seviyesinde. AI entegrasyonu, scraper altyapısı ve UI/UX vizyonu güçlü, ancak **güvenlik, ölçeklenebilirlik ve mimari temelde kritik eksiklikler** mevcut. Şu haliyle bir son kullanıcıya sunulursa, veri kaybı, güvenlik ihlali ve kullanıcı güveni kaybı riski yüksek.

> **Verdict:** Potansiyel yüksek. Teknik borç orta-yüksek. Beta'ya hazırlık süresi tahmini: **6-8 hafta** (temel eksiklikler kapatılırsa).

---

## 1. ŞU AN NE HALDEYİZ? (SAĞLIK TARAMASI)

### 1.1 Mevcut Mimari Değerlendirmesi

| Bileşen | Teknoloji | Değerlendirme | Risk Seviyesi |
|---------|-----------|---------------|---------------|
| **Backend API** | FastAPI + SQLAlchemy | ✅ Modern, hızlı, iyi yapılandırılmış | 🟢 Düşük |
| **Veritabanı** | SQLite (SQLAlchemy ORM) | ⚠️ Geliştirme için uygun, üretim için YETERSİZ | 🔴 Kritik |
| **Frontend** | React 19 + Vite + Anime.js | ✅ Hızlı, modern, estetik vizyon güçlü | 🟢 Düşük |
| **AI Motor** | Gemini 2.0 Flash | ✅ Başarılı entegrasyon, fallback mekanizmaları var | 🟡 Orta |
| **Scraping** | Playwright (async) | ✅ Async yapı doğru. Ancak anti-bot riski yüksek | 🟡 Orta |
| **Güvenlik** | Fernet şifreleme + CORS | ⚠️ Şifreleme var ama kimlik doğrulama YOK | 🔴 Kritik |
| **Otomasyon** | APScheduler + Gmail IMAP/SMTP | ⚠️ Çalışıyor ama thread/async karmaşası var | 🟡 Orta |
| **State Yönetimi** | React useState (App.jsx) | ⚠️ Tek dosyada 500+ satır. Context/Redux gerekli | 🟡 Orta |

### 1.2 Backend-Frontend Bağlantı Kuvveti

**Bağlantı Kuvveti: 6/10** — *"İletişim var ama güvenilirlik zayıf"*

**Güçlü Yönler:**
- API istek/yanıt yapısı tutarlı (`api.js` wrapper'ı iyi tasarlanmış)
- CORS yapılandırması bilinçli (`allow_methods` kısıtlı)
- FormData ve JSON istekleri doğru ayrılmış
- HTTP status kodları tutarlı kullanılıyor

**Zayıf Yönler:**
- **Kimlik doğrulama token'ı YOK.** Tüm API'ler açık. Herhangi bir script ile tüm veriler çekilebilir.
- `user_id = 1` hardcoded. Çok kullanıcılı yapıya geçişte **kökten refactor** gerekir.
- Frontend hata yönetimi yüzeysel. `console.warn` ile geçiştiriyor.
- Sayfalama (pagination) yok. 1000 ilan geldiğinde frontend çöker.

### 1.3 Beta Sunumuna Yakınlık

| Kriter | Durum | Eksiklik |
|--------|-------|----------|
| Temel CRUD işlemleri | ✅ Tamam | — |
| AI analizi | ✅ Tamam | — |
| UI/UX tasarımı | ✅ Premium his | Mobil uyum düşük |
| Güvenlik | 🔴 Kritik Eksik | JWT/OAuth yok, yetkilendirme yok |
| Veritabanı güvenilirliği | 🔴 Kritik Eksik | SQLite = veri kaybı riski |
| Hata toleransı | 🟡 Zayıf | Scraper hataları sessizce bastırılıyor |
| Test kapsamı | 🔴 Sıfır | Unit test, integration test yok |
| Deployment hazırlığı | 🔴 Yok | Dockerfile, CI/CD, environment config eksik |

**Beta Kararı:** ❌ **Şu an beta sunulmamalı.** Güvenlik ve veri kaybı riskleri çok yüksek.

---

## 2. NE YAPMALIYIZ? (STRATEJİK YOL HARİTASI)

### 2.1 "Vurucu Özellik" (Killer Feature) Stratejisi

LinkedIn ve Kariyer.net'ten farklılaşmak için şu özelliklerden **biri** seçilmeli ve mükemmelleştirilmeli:

#### 🥇 Öneri: "Akıllı Başvuru Copilot'u"
> *"Sadece ilan bulma değil, başvuruyu senin adına hazırlayan, sen onaylayınca gönderen bir asistan."*

**Neden bu fark yaratır:**
- LinkedIn "Başvur" butonu sunar. Kariyer Ajanı, "başvuruyu senin için hazırlar + önyazı yazar + gönderir" sunar.
- Kullanıcıya "onay bekleme" süreci vererek kontrol hissini korur.
- AI'nin gerçek değeri burada ortaya çıkar: Otomasyon değil, **yaratıcı yardımcı**.

#### 🥈 Alternatif: "E-posta İstihbarat Merkezi"
> *"Gelen kutunu AI sürekli tarar, staj fırsatlarını, hackathon'ları, mülakat davetlerini otomatik çıkarır."*

**Neden işe yarar:**
- Kariyer fırsatları sadece ilan sitelerinde değil, e-postalarda da gizli.
- Rakiplerin hiçbirinde bu yok.
- Gmail IMAP altyapısı zaten kurulu.

### 2.2 Kullanıcı Deneyimini (UX) Mükemmelleştirme Dokunuşları

| Dokunuş | Teknoloji | Etki | Öncelik |
|---------|-----------|------|---------|
| **Gerçek Zamanlı Bildirimler** | WebSocket (Socket.io) | Kullanıcıya anlık geri bildirim | 🔴 Yüksek |
| **İlerleme Çubuğu / Adım Takibi** | React Stepper + Backend State | Başvuru süreci görselleştirme | 🟡 Orta |
| **PDF Önizleme & Düzenleme** | react-pdf + PDF.js | CV'yi tarayıcıda gör, AI önerilerini uygula | 🟡 Orta |
| **AI Sohbet Arayüzü** | Chat UI (react-chat-widget) | Kullanıcı doğal dilde "Bana yazılım işi bul" desin | 🟢 Düşük (nice-to-have) |
| **Dark/Light Theme Toggle** | CSS Variables | Erişilebilirlik ve tercih | 🟢 Düşük |
| **Sesli Geri Bildirim** | Web Speech API | "3 yeni iş ilanı bulundu" bildirimi | 🟢 Düşük |

### 2.3 Teknolojik Altyapı İyileştirmeleri

```
ŞU AN:                          HEDEF:
SQLite ──────────────────────►  PostgreSQL (veya Supabase)
Yok   ───────────────────────►  Redis (Cache + Celery Broker)
Yok   ───────────────────────►  JWT + OAuth2 (Kimlik doğrulama)
APScheduler ─────────────────►  Celery + Redis (Güvenli background job)
Tek sunucu ──────────────────►  Docker Compose (API + DB + Worker)
Yok   ───────────────────────►  Sentry (Hata izleme)
Print debug ─────────────────►  Structlog (Yapılandırılmış loglama)
```

---

## 3. NE YAPMAMALIYIZ? (KIRMIZI ÇİZGİLER)

### 🚫 Asla Devam Edilmemesi Gereken Mimari Hatalar

#### 1. SQLite ile Üretime Çıkmak
> **Risk:** Concurrent write'lar sonucu veritabanı kilitlenmesi, veri kaybı.  
> **Karar:** SQLite sadece geliştirme ortamında kalacak. PostgreSQL'e geçilecek.

#### 2. `user_id = 1` Hardcoding'i
> **Risk:** Çok kullanıcılı yapıya geçişte tüm router'ların yeniden yazılması gerekir.  
> **Karar:** Hemen JWT token'dan `current_user` alan bir dependency yazılacak.

#### 3. Kimlik Doğrulama Olmadan API Açmak
> **Risk:** Herhangi biri `/api/cvs/upload` ile istenilen dosyayı yükleyebilir.  
> **Karar:** Tüm router'lara `Depends(get_current_user)` zorunlu tutulacak.

#### 4. Scraper'ları Ana İş Parçacığında Çalıştırmak
> **Risk:** Playwright + 3 platform = 30+ saniye bloklama. API timeout alır.  
> **Karar:** Scraper'lar sadece Celery worker'da çalışacak. API sadece "görev kuyruğuna ekle" yapacak.

#### 5. E-posta Şifrelerini "Uygulama Şifresi" Olarak Plain Text Almak
> **Risk:** Kullanıcılar gerçek şifrelerini girebilir. Güvenlik ihlali.  
> **Karar:** OAuth2 (Gmail API) ile token-based auth kullanılacak. Şifre saklama kalkacak.

### 🚫 Uzak Durulması Gereken Teknolojiler

| Teknoloji/Yaklaşım | Neden Uzak Durmalıyız |
|--------------------|----------------------|
| **jQuery / Bootstrap** | React + custom CSS zaten var. Eski paradigmalar UI'ı bozar. |
| **Monolitik Frontend** | App.jsx 500+ satır. State management şart. |
| **Selenium** | Playwright zaten var. Selenium daha yavaş ve bakımsız. |
| **Kendi SMTP Sunucusu** | Gmail/Outlook SMTP'si yeterli. Kendi sunucu = SPAM listesi. |
| **GraphQL (şimdilik)** | REST yeterli. Over-engineering yapmayın. |
| **Mikroservisler** | Monolit iyi çalışıyor. 1 geliştirici için mikroservis = intihar. |

---

## 4. TEKNİK BORÇ (TECHNICAL DEBT)

### 4.1 Kısa Vadeli (1-2 Hafta — Ağrıtmaya Başladı)

#### 🔴 Veritabanı: JSON String Kolonlar
```python
# Şu anki hatalı yaklaşım:
target_sectors = Column(Text, default='["Yapay Zeka"]')  # JSON as string

def get_target_sectors(self):
    return json.loads(self.target_sectors or "[]")
```
**Sorun:** Sorgulanamaz, indekslenemez, tip güvenliği yok.  
**Çözüm:** SQLAlchemy 2.0 `JSON` tipi kullanılacak veya PostgreSQL `jsonb`.

#### 🔴 Async/Senkron Karmaşası
```python
# scheduler.py
async def run_job_sync(db: Session):  # async fonksiyon
    ...

def sync_jobs_task():  # senkron fonksiyon
    asyncio.run(run_job_sync(db))  # Yeni event loop = risk
```
**Sorun:** APScheduler senkron çalışır. `asyncio.run()` her seferinde yeni loop açar. Veritabanı session'ları karışabilir.  
**Çözüm:** `AsyncIOScheduler` kullan veya Celery'e taşı.

#### 🔴 Exception Handling: `print()` ile Hata Bastırma
```python
except Exception as e:
    print(f"[-] Scraper error: {e}")
```
**Sorun:** Üretimde loglar kaybolur. Kritik hatalar farkedilmez.  
**Çözüm:** Python `logging` modülü + Sentry entegrasyonu.

### 4.2 Orta Vadeli (2-4 Hafta — İleride Başımızı Ağrıtır)

#### 🟡 Scraper Dayanıklılığı
- Kariyer.net HTML yapısı değişirse scraper çöker.
- LinkedIn zaten anti-bot önlemleriyle bloklar.
- **Çözüm:** Her scraper'a "yapı değişikliği" fallback'i ekle. HTML selector'lar dışarıdan config'lenebilir olsun.

#### 🟡 Gemini API Kota Yönetimi
```python
# Şu an sadece try/except var, kota yönetimi yok
```
**Sorun:** Ücretsiz Gemini kotası biterse tüm AI özellikleri anında devre dışı kalır.  
**Çözüm:** Rate limiter (Redis-based) + kota takip + kullanıcı başına limit.

#### 🟡 Dosya Yükleme Güvenliği
```python
# cv.py
if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(400, "Sadece PDF")
```
**Sorun:** Dosya uzantısı kolayca spoof edilebilir. Magic number kontrolü yok.  
**Çözüm:** `python-magic` ile MIME type doğrulama + ClamAV virüs taraması.

#### 🟡 CORS Yapılandırması
```python
_prod_origins = [
    "http://localhost:5173",  # Üretimde localhost?!?
]
```
**Sorun:** Üretim CORS ayarları geliştirme ile aynı.  
**Çözüm:** Gerçek domain eklenecek. `ALLOWED_ORIGINS` env'den okunacak.

### 4.3 Uzun Vadeli (1-3 Ay — Stratejik Risk)

#### 🟠 Çoklu Kullanıcı Desteği
Şu anki tüm kod tek kullanıcı (`user_id=1`) için yazılmış. Çoklu kullanıcıya geçiş:
- Veritabanı: Her tabloya `user_id` eklemek
- AI: Kullanıcı başına prompt context yönetimi
- Dosyalar: Kullanıcı bazlı klasör yapısı
- Görevler: Kullanıcı bazlı kuyruk yönetimi

**Maliyet:** 2-3 hafta full refactor.

#### 🟠 Ölçeklenebilirlik Sınırı
- SQLite + tek sunucu = ~100 eşzamanlı kullanıcıda performans düşüşü
- AI istekleri senkron = uzun bekleme süreleri
- Scraper'lar aynı IP'den = IP ban riski

#### 🟠 Yasal ve Etik Riskler
- Web scraping: Kariyer.net ve LinkedIn Terms of Service'ı ihlal edebilir.
- Otomatik e-posta gönderimi: Spam yasalarına (CAN-SPAM, KVKK) aykırı olabilir.
- Kullanıcı verileri: KVKK/GDPR uyumu sağlanmalı.

---

## 5. ÖNERİLEN YOL HARİTASI (ROADMAP)

### Faz 1: Güvenlik ve Temel Altyapı (2 Hafta)
- [ ] PostgreSQL geçişi
- [ ] JWT + OAuth2 kimlik doğrulama
- [ ] Şifre yerine Gmail OAuth token
- [ ] `.env` yapılandırması ve secret yönetimi
- [ ] Docker Compose setup (API + DB + Redis)

### Faz 2: Teknik Borç Temizliği (2 Hafta)
- [ ] SQLite → PostgreSQL migrasyonu
- [ ] JSON string kolonlar → JSONB
- [ ] APScheduler → Celery + Redis
- [ ] Global exception handler + Sentry
- [ ] Unit test altyapısı (pytest)

### Faz 3: Ölçeklenebilirlik (2 Hafta)
- [ ] API rate limiting (SlowAPI)
- [ ] Redis caching (AI yanıtları, scraper sonuçları)
- [ ] Dosya depolama: AWS S3 / local → object storage
- [ ] Background job monitoring (Flower)

### Faz 4: Beta Özellikleri (2 Hafta)
- [ ] WebSocket gerçek zamanlı bildirimler
- [ ] PDF önizleme ve AI düzenleme önerileri
- [ ] Mobil responsive iyileştirmeler
- [ ] Onboarding flow (ilk kullanıcı deneyimi)

---

## 6. SONUÇ ve TAVSİYELER

### Güçlü Yönler (Koruyun)
1. **AI Entegrasyonu:** Gemini fallback mekanizmaları düşünülmüş. Prompt'lar yapılandırılmış.
2. **UI/UX Vizyonu:** Cyberpunk/HUD teması özgün ve akılda kalıcı.
3. **Modüler Backend:** Router, model, scraper ayrımı temiz.
4. **Güvenlik Farkındalığı:** Fernet şifreleme, CORS, request size limit düşünülmüş.

### Kritik Eksiklikler (Hemen Çözün)
1. **Kimlik doğrulama yok.** Bu, ürün olarak sunulamaz.
2. **SQLite üretim için değil.** Veri kaybı kaçınılmaz.
3. **Test yok.** Her refactor regresyon riski taşır.

### Stratejik Tavsiye
> **"Mükemmeli beklemeyin, güvenliği bekleyin."**  
> AI özellikleri zaten çalışıyor. UI zaten etkileyici. Ama **güvenlik ve veri bütünlüğü olmadan** bunların hiçbir değeri yok.

**Önerilen Hedef:** 6 hafta içinde "güvenli beta" sunumuna hazır hale getirin. Özellik eklemeyi bırakın, temeli sağlamlaştırın.

---

*Rapor hazırlayan: CTO / Teknoloji Başkanı*  
*Sonraki adım: Faz 1 görev listesinin detaylandırılması ve sprint planlaması*

