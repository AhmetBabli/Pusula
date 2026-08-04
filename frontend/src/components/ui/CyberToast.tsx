import React, { useEffect, useRef } from 'react';
import './CyberToast.css';

const CyberToast = ({ message, type = 'success', duration = 4000, onClose }) => {
  const timerRef = useRef(null);

  // Sayacı başlatan fonksiyon
  const startTimer = () => {
    timerRef.current = setTimeout(() => {
      onClose();
    }, duration);
  };

  // Sayacı durduran fonksiyon
  const clearTimer = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  // Bileşen yüklendiğinde sayacı başlat, unmount olduğunda temizle
  useEffect(() => {
    if (message) startTimer();
    
    return () => clearTimer();
  }, [message, duration, onClose]);

  if (!message) return null;

  // Erişilebilirlik (A11y) standartları
  const role = type === 'error' ? 'alert' : 'status';
  const ariaLive = type === 'error' ? 'assertive' : 'polite';

  return (
    <div 
      className={`cyber-toast toast-${type}`}
      role={role}
      aria-live={ariaLive}
      onMouseEnter={clearTimer} // UX: Fare üzerine gelince sayacı durdur (kapanmasın)
      onMouseLeave={startTimer} // UX: Fare çekilince sayacı tekrar başlat
    >
      <div className="toast-content">
        {/* Dekoratif ikonları ekran okuyuculardan gizliyoruz */}
        <span className="toast-icon" aria-hidden="true">
          {type === 'success' ? '✓' : type === 'error' ? '×' : 'ℹ'}
        </span>
        <span className="toast-message">{message}</span>
      </div>
      
      {/* UX: Kullanıcıya beklemeden kapatma özgürlüğü veriyoruz */}
      <button 
        className="toast-close-btn" 
        onClick={onClose}
        aria-label="Kapat"
      >
        ✕
      </button>

      {/* Dinamik CSS: Progress bar süresi JS ile her zaman senkron kalacak */}
      <div 
        className="toast-progress-bar"
        style={{ animationDuration: `${duration}ms` }} 
      />
    </div>
  );
};

export default CyberToast;