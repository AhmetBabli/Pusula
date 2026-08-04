import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

def list_supported_models():
    """Gemini API üzerindeki generateContent destekli modelleri listeler."""
    
    # 1. Çevre değişkenlerini dinamik bul ve yükle
    load_dotenv(find_dotenv())
    
    # 2. Fail-Fast: API anahtarının varlığını doğrula
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[-] KRİTİK HATA: GEMINI_API_KEY bulunamadı!")
        print("    Lütfen .env dosyanızı ve değişken adını kontrol edin.")
        sys.exit(1) # Hata koduyla sistemden çık
        
    # Konfigürasyonu ayarla
    genai.configure(api_key=api_key)

    print("🚀 Gemini API: Desteklenen Modeller Taranıyor...")
    print("-" * 50)
    
    try:
        count = 0
        # API'den modelleri çek
        for model in genai.list_models():
            # Yalnızca metin/içerik üretimi destekleyen modelleri filtrele
            if 'generateContent' in model.supported_generation_methods:
                print(f"✅ {model.name}")
                count += 1
                
        print("-" * 50)
        print(f"Toplam {count} adet model bulundu ve kullanıma hazır.")
        
    except Exception as e:
        print(f"[-] Modeller listelenirken ağ veya yetki hatası oluştu:\n    {e}")
        sys.exit(1)

if __name__ == "__main__":
    list_supported_models()