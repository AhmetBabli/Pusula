import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import './CyberModal.css';

const CyberModal = ({ isOpen, onClose, title, children }) => {
  useEffect(() => {
    if (!isOpen) return;

    // 1. Zıplama Bug'ını Çözmek İçin Scrollbar Genişliğini Hesapla
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    
    // Orijinal stilleri hafızaya al
    const originalOverflow = document.body.style.overflow;
    const originalPaddingRight = document.body.style.paddingRight;

    // Scroll'u kilitle ve boşalan scrollbar genişliği kadar sağdan padding ver (Zıplamayı önler)
    document.body.style.overflow = 'hidden';
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }

    // 2. UX: Escape Tuşu ile Kapatma Dinleyicisi
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    // Bileşen kapandığında (Cleanup) her şeyi eski haline çevir
    return () => {
      document.body.style.overflow = originalOverflow;
      document.body.style.paddingRight = originalPaddingRight;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || typeof document === 'undefined') return null;

  const modalContent = (
    <div 
      className="cyber-modal-overlay" 
      onClick={onClose}
      // 3. Erişilebilirlik (A11y) İyileştirmeleri
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="cyber-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="cyber-modal-header">
          <h2 id="modal-title" className="cyber-modal-title">{title}</h2>
          <button 
            className="cyber-modal-close" 
            onClick={onClose}
            aria-label="Modalı Kapat" // Ekran okuyucular için
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div className="cyber-modal-body">
          {children}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.getElementById('modal-root') || document.body);
};

export default CyberModal;