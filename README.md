# 🎯 Kariyer Ajanı

AI destekli kariyer asistanı — staj/iş ilanlarını otomatik tarıyor, CV'lerini yönetiyor, şirkete özel motivasyon mektubu yazıyor ve başvuruları senin onayınla gönderiyor.

## 🚀 Hızlı Başlangıç

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📁 Proje Yapısı

```
kariyer-ajani/
├── backend/
│   ├── main.py              # FastAPI uygulaması
│   ├── config.py             # Ayarlar
│   ├── database.py           # SQLAlchemy kurulumu
│   ├── models/               # Veritabanı modelleri
│   ├── routers/              # API endpoint'leri
│   ├── ai/                   # Gemini AI entegrasyonu
│   ├── scrapers/             # Web scraper'lar
│   └── automation/           # Başvuru otomasyonu
├── frontend/                 # React + Vite arayüz
├── cv_store/                 # CV dosyaları (PDF)
├── .env                      # Ortam değişkenleri
└── README.md
```

## 🔑 Ortam Değişkenleri

`.env.example` dosyasını `.env` olarak kopyalayıp doldurun:
```
GEMINI_API_KEY=your_key_here
```

## 📊 API Dökümantasyonu

Sunucu çalışırken: [http://localhost:8000/docs](http://localhost:8000/docs)
