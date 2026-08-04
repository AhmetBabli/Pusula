import React, { useRef, useEffect } from 'react';
import * as animeModule from 'animejs';

const anime = animeModule.default || animeModule;

export default function StickyNote({ color = 'yellow', title, value, label, children, className = '', style = {} }) {
  const noteRef = useRef(null);

  useEffect(() => {
    const el = noteRef.current;
    if (!el) return;

    let ticking = false; // requestAnimationFrame için kilit mekanizması

    const updateTransform = (e) => {
      const rect = el.getBoundingClientRect();
      const x = e.clientX - rect.left; 
      const y = e.clientY - rect.top; 
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = ((y - centerY) / centerY) * -15; 
      const rotateY = ((x - centerX) / centerX) * 15;

      // Önceki yarım kalan animasyonları temizle ki motor kasmasın
      anime.remove(el);

      anime({
        targets: el,
        rotateX: rotateX,
        rotateY: rotateY,
        translateZ: 30, 
        scale: 1.05,
        duration: 150, // Süreyi kısalttık çünkü zaten fareyi takip ediyor
        easing: 'easeOutQuad'
      });
      
      el.style.boxShadow = `${-rotateY}px ${rotateX + 10}px 20px rgba(0,0,0,0.15)`;
      ticking = false; // Animasyon çizildi, kilidi aç
    };

    const handleMouseMove = (e) => {
      // Fare 1000 kez tetiklese bile ekranın yenilenme hızına (FPS) göre çizim yap
      if (!ticking) {
        window.requestAnimationFrame(() => updateTransform(e));
        ticking = true;
      }
    };

    const handleMouseLeave = () => {
      anime.remove(el); // Takip animasyonunu durdur
      
      anime({
        targets: el,
        rotateX: 0,
        rotateY: 0,
        translateZ: 0,
        scale: 1,
        duration: 800,
        easing: 'easeOutElastic(1, .6)' // Bouncy (elastik) dönüş
      });
      
      // Gölgeyi varsayılan hale pürüzsüzce geri döndür
      el.style.boxShadow = '0px 10px 20px rgba(0,0,0,0.05)';
    };

    el.addEventListener('mousemove', handleMouseMove);
    el.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      el.removeEventListener('mousemove', handleMouseMove);
      el.removeEventListener('mouseleave', handleMouseLeave);
      anime.remove(el); // Component silinirse (unmount) bellek sızıntısını önle
    };
  }, []);

  return (
    <div 
      className={`sticky-note-wrapper ${className}`} 
      style={{ perspective: '1000px', ...style }}
    >
      <div 
        ref={noteRef} 
        className={`sticky-note ${color}`} 
        style={{ 
          transformOrigin: 'center center', 
          willChange: 'transform',
          /* JS sürekli güncellediği için buradaki box-shadow transition'ını sildik */
          width: '100%',
          height: '100%',
          boxShadow: '0px 10px 20px rgba(0,0,0,0.05)' // Başlangıç gölgesi
        }}
      >
        {title && <div className="note-title">{title}</div>}
        {value !== undefined && <div className="note-value">{value}</div>}
        {label && <div className="note-label">{label}</div>}
        {children}
      </div>
    </div>
  );
}