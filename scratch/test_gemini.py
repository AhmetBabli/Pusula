import asyncio
import json
import logging
import os
from dotenv import load_dotenv, find_dotenv

# 1. Çevre değişkenlerini dinamik ve güvenli bir şekilde yükle
# find_dotenv() klasör ağacında yukarı doğru çıkarak .env dosyasını otomatik bulur
load_dotenv(find_dotenv())

# Diğer içe aktarmalar .env yüklendikten SONRA yapılır (Settings modülünün patlamaması için)
from backend.ai.gemini_client import analyze_cv_ats

# Loglama ayarı (Hataları görmek için)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def test_analyze_cv():
    """Gemini ATS Analiz fonksiyonunu test eder."""
    
    # Çok kısa metinler AI'ın fallback (basit) algoritmaya düşmesine neden olabilir,
    # bu yüzden biraz daha gerçekçi bir dummy text kullanıyoruz.
    test_text = """
    Ahmet Culcu - Özgeçmiş
    Yönetim Bilişim Sistemleri (YBS) 3. sınıf öğrencisi. 
    Teknolojiler: Python, SQL, React, JavaScript, Git.
    Deneyim: Bir yazılım şirketinde 3 ay staj yaptım. Veritabanı analizi görevlerinde bulundum.
    Projeler: React ve Python kullanarak tam zamanlı çalışan bir e-ticaret otomasyonu geliştirdim.
    """
    
    print("🚀 Test Başlıyor: Gemini AI CV Analizi...")
    print("-" * 50)
    
    try:
        # Fonksiyonu asenkron olarak çağır
        result = await analyze_cv_ats(test_text)
        
        # Sonucu okunabilir formatta (Pretty Print) terminale bas
        # ensure_ascii=False ile Türkçe karakterlerin (ş, ğ, ı) düzgün görünmesini sağlıyoruz
        formatted_result = json.dumps(result, indent=4, ensure_ascii=False)
        
        print("✅ Analiz Başarılı! Sonuç:\n")
        print(formatted_result)
        
    except Exception as e:
        logging.error(f"Test sırasında beklenmeyen bir hata oluştu: {e}")

if __name__ == "__main__":
    # Testi çalıştır
    asyncio.run(test_analyze_cv())