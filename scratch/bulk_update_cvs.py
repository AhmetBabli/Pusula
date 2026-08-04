import asyncio
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Ortam değişkenlerini otomatik bul ve yükle
load_dotenv(find_dotenv())

# Proje kök dizinini dinamik olarak PYTHONPATH'e ekle
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.ai.gemini_client import analyze_cv_ats
from backend.database import SessionLocal
from backend.models.cv import CV

# Loglama ayarları (Sunucuda veya terminalde profesyonel takip için)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def bulk_update():
    logging.info("🚀 Toplu CV AI Analiz Güncellemesi Başlatılıyor...")
    
    db = SessionLocal()
    try:
        # 1. OPTİMİZASYON: Sadece metni olan CV'leri çek. 
        cvs_with_text = db.query(CV).filter(CV.extracted_text.isnot(None)).all()
        
        # 2. FİLTRELEME: Zaten analiz edilmiş olanları ve metni çok kısa olanları atla
        pending_cvs = [
            cv for cv in cvs_with_text 
            if len(cv.extracted_text.strip()) > 50 and not cv.ats_score
        ]
        
        if not pending_cvs:
            logging.info("Güncellenecek yeni CV bulunamadı. Tüm kayıtlar güncel!")
            return

        logging.info(f"Analiz edilecek {len(pending_cvs)} adet bekleyen CV bulundu.")
        print("-" * 50)

        # 3. İŞLEME DÖNGÜSÜ
        for index, cv in enumerate(pending_cvs, 1):
            logging.info(f"[{index}/{len(pending_cvs)}] İşleniyor -> ID: {cv.id} | Başlık: {cv.title}")
            
            try:
                # Gemini API Çağrısı
                result = await analyze_cv_ats(cv.extracted_text)
                
                # Modeli güncelle
                cv.ats_score = result.get("score", 0)
                cv.ats_feedback = result.get("feedback", "")
                cv.strengths = json.dumps(result.get("strengths", []), ensure_ascii=False)
                cv.weaknesses = json.dumps(result.get("weaknesses", []), ensure_ascii=False)
                cv.target_keywords = json.dumps(result.get("keywords", []), ensure_ascii=False)
                
                # Başarılıysa DB'ye yaz
                db.commit()
                logging.info(f"✅ Başarılı! (Skor: {cv.ats_score})")
                
                # 4. RATE LIMIT KORUMASI (Çok Önemli!)
                # Son eleman değilsek API'yi boğmamak için bekle
                if index < len(pending_cvs):
                    logging.info("API kotası için 4 saniye bekleniyor...")
                    await asyncio.sleep(4)
                    
            except Exception as e:
                # 5. TRANSACTION KURTARMA (Zehirli Session'ı Temizle)
                db.rollback()
                logging.error(f"❌ Hata! CV ID: {cv.id} güncellenemedi: {e}")
                logging.info("Bir sonraki CV'ye geçiliyor...")

    except Exception as e:
        logging.critical(f"Kritik veritabanı veya sistem hatası: {e}")
        
    finally:
        # 6. GÜVENLİ KAPANIŞ
        db.close()
        print("-" * 50)
        logging.info("Veritabanı bağlantısı kapatıldı. Görev tamamlandı.")

if __name__ == "__main__":
    # Python 3.7+ güvenli asenkron çalışma mantığı
    try:
        asyncio.run(bulk_update())
    except KeyboardInterrupt:
        logging.warning("Kullanıcı tarafından işlem yarıda kesildi (CTRL+C).")