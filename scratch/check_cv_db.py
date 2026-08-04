import sys
from backend.database import SessionLocal
from backend.models.cv import CV

def inspect_cvs(limit: int = 20):
    """
    Veritabanındaki CV kayıtlarını güvenli bir şekilde listeler.
    Büyük veri setlerinde belleği korumak için varsayılan limit 20'dir.
    """
    print("🔍 CV Veritabanı İnceleyicisi Başlatıldı...\n")
    
    # Session (Oturum) başlatılıyor
    db = SessionLocal()
    
    try:
        # Bellek şişmesini önlemek için limit uygulanıyor
        cvs = db.query(CV).limit(limit).all()
        
        if not cvs:
            print("[!] Veritabanında henüz hiç CV kaydı bulunamadı.")
            return

        print(f"Toplam {len(cvs)} adet CV listeleniyor:")
        print("=" * 50)

        for cv in cvs:
            print(f"ID         : {cv.id}")
            print(f"Title      : {cv.title}")
            
            # NoneType hatalarını önlemek için güvenli okuma
            text_len = len(cv.extracted_text) if cv.extracted_text else 0
            print(f"Text Length: {text_len} karakter")
            
            # ATS Score None olabilir, varsayılan değer atama
            score = cv.ats_score if cv.ats_score is not None else "Hesaplanmamış"
            print(f"ATS Score  : {score}")
            
            # Feedback None ise patlamaması için (or "") yapısı kullanılıyor
            feedback_text = cv.ats_feedback or "Geri bildirim henüz yok."
            # Sadece tek satırda 100 karakter göster, satır sonlarını temizle
            clean_feedback = feedback_text.replace("\n", " ")
            print(f"Feedback   : {clean_feedback[:100]}...")
            
            print("-" * 50)

    except Exception as e:
        print(f"[-] Veritabanı sorgusu sırasında beklenmeyen hata:\n{e}")
        sys.exit(1)
        
    finally:
        # Kod başarılı olsa da, hata alsa da Session KESİNLİKLE kapatılır!
        db.close()
        print("✅ Veritabanı bağlantısı güvenle kapatıldı.")

if __name__ == "__main__":
    inspect_cvs()