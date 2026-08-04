# 🎨 KARİYER AJANI — FRONTEND REVAMP PLANI

## Mevcut Sorunlar
1. **App.jsx 500+ satır** — Tek dosyada her şey, bakımı zor
2. **Dashboard yok** — Backend'de `/dashboard/stats` var ama kullanılmıyor
3. **Detay sayfaları yok** — İş ilanına tıklayınca açıklama görünmüyor, CV'ye tıklayınca içerik yok
4. **Etkinlikler (Events) eksik** — Backend'de var, UI'da yok
5. **Filtreleme/Arama yok** — 100 ilan olduğunda hepsini kaydırmak gerek
6. **Başvuru takibi yetersiz** — Sadece "bekleyen" var, geçmiş başvurular yok
7. **Responsive zayıf** — Mobil kullanım zor
8. **Loading/Error UI yetersiz** — Sadece spinner var

---

## ✅ Revizyon Adımları

### Adım 1: Component Yapılandırması (Mimari)
App.jsx'i parçalara ayır:
```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Header.jsx         # Üst bar (profil, status)
│   │   ├── Navigation.jsx     # Alt navigasyon
│   │   └── BootScreen.jsx     # Açılış animasyonu
│   ├── dashboard/
│   │   ├── DashboardView.jsx  # Ana ekran (istatistikler)
│   │   └── StatCard.jsx       # Tek istatistik kutusu
│   ├── jobs/
│   │   ├── JobsView.jsx       # İş ilanları listesi
│   │   ├── JobCard.jsx        # Tek ilan kartı
│   │   └── JobDetailModal.jsx # İlan detay modalı
│   ├── cv/
│   │   ├── CVView.jsx         # CV listesi
│   │   ├── CVCard.jsx         # Tek CV kartı
│   │   └── CVDetailModal.jsx  # CV detay/önizleme
│   ├── inbox/
│   │   ├── InboxView.jsx      # Gelen kutusu
│   │   └── InboxItem.jsx      # Tek e-posta öğesi
│   ├── applications/
│   │   ├── ApplicationsView.jsx # Başvuru takip
│   │   └── ApplicationTimeline.jsx # Başvuru adım çubuğu
│   └── modals/
│       ├── ProfileModal.jsx
│       ├── UploadCVModal.jsx
│       ├── GmailModal.jsx
│       └── OutreachModal.jsx
```

### Adım 2: Dashboard Ekranı (Yeni)
- Toplam ilan, bekleyen başvuru, yeni e-posta sayısı
- En iyi eşleşen 5 ilan önizlemesi
- Son aktivite zaman çizelgesi
- Hızlı aksiyon butonları (Tara, Senkronize et)

### Adım 3: Detay Modalı İyileştirmeleri
**İş İlanı Detayı:**
- Tam açıklama görüntüleme
- Gereksinimler listesi
- AI Eşleşme Skoru + Açıklaması
- Eksik beceriler listesi
- "Başvuru Hazırla" butonu (AI motivasyon mektubu üretir)
- Kaynak platform linki

**CV Detayı:**
- PDF önizleme / Metin görüntüleme
- ATS Skoru + Geri Bildirim
- Güçlü/Zayıf yönler listesi
- AI İyileştirme Önerileri
- "Varsayılan Yap" butonu

### Adım 4: Etkinlikler (Events) Sekmesi
- Yaklaşan kariyer etkinlikleri, fuarlar, hackathonlar
- Tarih sıralaması
- Hatırlatma ekleme

### Adım 5: Filtreleme & Arama
- İş ilanları: Sektör, konum, skor aralığı, kaynak platform
- CV'ler: Varyant tipi, ATS skoru
- Arama çubuğu (başlık ve şirket adı)
- Sıralama: Skor, tarih, şirket

### Adım 6: Başvuru Takip İyileştirmesi
- Tüm başvuruların zaman çizelgesi (draft → onay → gönderildi)
- Adım adım görsel takip
- Reddedilen başvuruların nedenleri
- Tekrar başvur butonu

### Adım 7: UI/UX İyileştirmeleri
- **Skeleton Loading** — Veri yüklenirken iskelet ekran
- **Boş Durum İllüstrasyonları** — "Henüz ilan yok" gibi durumlarda ikon + açıklama
- **Hata Durumları** — API hatası olduğunda retry butonu
- **Toast Bildirimleri** — Daha zengin (başarı, hata, uyarı, bilgi)
- **Mikro Animasyonlar** — Buton hover, kart girişi, sayı sayaçları

### Adım 8: Responsive Tasarım
- Mobilde alt navigasyon → hamburger menü
- Kartlar tek sütun
- Modal tam ekran
- Dokunmatik dostu butonlar

---

## 📅 Tahmini Süre
- Adım 1-2: 1 gün (Mimari + Dashboard)
- Adım 3: 1 gün (Detay modalı)
- Adım 4-5: 1 gün (Events + Filtreleme)
- Adım 6: 0.5 gün (Başvuru takip)
- Adım 7-8: 1 gün (UI/UX + Responsive)

**Toplam: ~4.5 gün**

---

## 🚫 Yapılmayacaklar (Kapsam Dışı)
- Kimlik doğrulama (tek kullanıcı)
- Veritabanı değişikliği
- Backend API değişikliği (var olanları kullanacağız)
- WebSocket (şimdilik polling yeterli)

