import React, { useState, useEffect } from 'react';
import { Terminal, CheckCircle, Activity, Search, Brain, Send } from 'lucide-react';

// 1. Yardımcı Zaman Fonksiyonu: Kodu temiz tutar ve tekrarı önler
const getCurrentTimeStr = () => {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
};

// 2. Statik Veriyi Dışarı Alma: Bileşen her render edildiğinde baştan yaratılmasını engeller (Bellek Optimizasyonu)
const ACTIVITIES = [
  { text: 'LinkedIn üzerinde yeni ilanlar aranıyor...', icon: <Search size={14} /> },
  { text: 'Kariyer.net verileri senkronize ediliyor...', icon: <Search size={14} /> },
  { text: 'E-postalar AI tarafından analiz ediliyor...', icon: <Brain size={14} /> },
  { text: 'CV ve iş eşleşmeleri hesaplanıyor...', icon: <Activity size={14} /> },
  { text: 'Uygun ilanlar için motivasyon mektubu taslaklanıyor...', icon: <Send size={14} /> },
  { text: 'Tarama döngüsü tamamlandı. 3 yeni fırsat bulundu.', icon: <CheckCircle size={14} /> },
];

const ProtocolTracker = ({ isRunning }) => {
  const [logs, setLogs] = useState([]);

  // 3. Dinamik Başlangıç: Bileşen ilk mount olduğunda GERÇEK zamanı alarak inandırıcılığı korur
  useEffect(() => {
    setLogs([
      { id: 'init-1', time: getCurrentTimeStr(), text: 'Sistem başlatıldı. AI Çekirdeği çevrimiçi.', type: 'info', icon: <Terminal size={14} /> },
      { id: 'init-2', time: getCurrentTimeStr(), text: 'İstihbarat ağına bağlanıldı.', type: 'success', icon: <Activity size={14} /> },
    ]);
  }, []);

  useEffect(() => {
    if (!isRunning) return;

    let index = 0;
    const interval = setInterval(() => {
      if (index < ACTIVITIES.length) {
        
        const newLog = {
          id: crypto.randomUUID(), // Date.now() yerine çakışma ihtimali sıfır olan modern ID üretimi
          time: getCurrentTimeStr(),
          text: ACTIVITIES[index].text,
          icon: ACTIVITIES[index].icon,
        };

        setLogs(prev => [...prev, newLog].slice(-6)); // Sadece son 6 log
        index++;
      } else {
        clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="protocol-log">
      {logs.map((log, index) => {
        // 4. Doğru 'Active' Mantığı: Sadece animasyon çalışıyorsa ve log dizideki EN SON elamansa parlasın
        const isActive = isRunning && index === logs.length - 1;
        
        return (
          <div key={log.id} className={`log-entry ${isActive ? 'active' : ''}`}>
            <span className="timestamp">[{log.time}]</span>
            <span className="icon">{log.icon}</span>
            <span className="text">{log.text}</span>
          </div>
        );
      })}
    </div>
  );
};

export default ProtocolTracker;