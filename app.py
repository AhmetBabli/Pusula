"""
🎯 Kariyer Ajanı — Full-Stack Başlatıcı
Kullanım: python app.py
"""
import subprocess
import time
import os
import sys
import webbrowser
import signal
import atexit

# Terminalde emoji/UTF-8 karakter basarken oluşan çökmeleri (UnicodeEncodeError) önler
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Global süreç listesi (temizlik için)
PROCESSES = []

def cleanup():
    """Tüm kaydedilmiş süreç ağaçlarını güvenle temizler."""
    if not PROCESSES:
        return
        
    print("\n[!] Kapatılıyor... Zombi süreçler temizleniyor...")
    for proc in PROCESSES:
        try:
            # Sürecin hala yaşayıp yaşamadığını kontrol et
            if proc.poll() is None:
                if sys.platform == "win32":
                    subprocess.call(
                        ['taskkill', '/F', '/T', '/PID', str(proc.pid)], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL
                    )
                else:
                    # Unix sistemlerinde Process Group ID'sini öldürerek tüm ağacı temizle
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception as e:
            print(f"[-] Süreç kapatılırken önemsiz hata (PID: {proc.pid}): {e}")
            
    PROCESSES.clear()
    print("✅ Sistem güvenle kapatıldı.")

# Normal çıkışlarda veya hata durumlarında cleanup'ı garanti altına al
atexit.register(cleanup)

def handle_signals(signum, frame):
    """İşletim sisteminden gelen kill sinyallerini yakalar."""
    cleanup()
    sys.exit(0)

def get_project_root():
    """Scriptin nerede çalıştırıldığından bağımsız olarak kök dizini bulur."""
    return os.path.dirname(os.path.abspath(__file__))

def start_services():
    # Unix sistemlerinde kill sinyallerini yakalamak için bağla
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, handle_signals)
        signal.signal(signal.SIGINT, handle_signals)

    print("🎯 Kariyer Ajanı — Sistemler ayağa kaldırılıyor...")
    print("-" * 50)
    
    project_root = get_project_root()

    # 1. Backend'i başlat
    print("[+] Backend (API) başlatılıyor...")
    backend_kwargs = {
        "cwd": project_root
    }
    
    if sys.platform == "win32":
        backend_kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        # Unix'te Process Group oluştur (Sonradan topluca öldürebilmek için)
        backend_kwargs["preexec_fn"] = os.setsid
        
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        **backend_kwargs
    )
    PROCESSES.append(backend_process)

    # Backend'in ayağa kalkması için kısa bir süre bekle
    time.sleep(3)

    # 2. Frontend'i başlat
    print("[+] Frontend (Dashboard) başlatılıyor...")
    frontend_dir = os.path.join(project_root, "frontend")
    
    # Frontend dizini var mı kontrolü
    if not os.path.exists(frontend_dir):
        print(f"[-] HATA: Frontend dizini bulunamadı -> {frontend_dir}")
        sys.exit(1)
        
    frontend_kwargs = {
        "cwd": frontend_dir,
        "shell": sys.platform == "win32"
    }
    
    if sys.platform == "win32":
        frontend_kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        frontend_kwargs["preexec_fn"] = os.setsid

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        **frontend_kwargs
    )
    PROCESSES.append(frontend_process)

    print("-" * 50)
    print("✅ Tüm servisler çalışıyor!")
    print("🔗 API UI: http://localhost:8000/docs")
    print("🔗 Dashboard: http://localhost:5173")
    print("\n[!] Durdurmak için bu terminalde CTRL+C yapabilirsin.")
    
    time.sleep(2)
    # Tarayıcıyı açarken ufak bir hata yönetimi (bazen sistemde default tarayıcı tanımlı olmaz)
    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        print("[!] Tarayıcı otomatik açılamadı, lütfen linke tıklayın.")

    try:
        # Ana script'in kapanmaması için bekle
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        # cleanup() atexit sayesinde otomatik çalışacak, burada pass geçebiliriz
        pass

if __name__ == "__main__":
    start_services()