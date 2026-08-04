import React, { useEffect, useRef } from 'react';
import * as animeModule from 'animejs';

const anime = animeModule.default || animeModule;

function BootScreen({ onComplete }) {
  const overlayRef = useRef(null);
  const logoRef = useRef(null);
  const progressRef = useRef(null);

  useEffect(() => {
    // Animasyon tamamlandığında yapılacak işlemler
    const handleAnimationComplete = () => {
      // ÖNEMLİ: Elementi tamamen gizle ki alttaki butonlara tıklanabilsin
      if (overlayRef.current) {
        overlayRef.current.style.display = 'none';
      }
      if (onComplete) onComplete();
    };

    const tl = anime.timeline({
      easing: 'easeOutExpo',
      complete: handleAnimationComplete
    });

    tl.add({
      targets: logoRef.current,
      opacity: [0, 1],
      scale: [0.8, 1],
      duration: 600,
    })
    .add({
      targets: progressRef.current,
      width: ['0%', '100%'],
      duration: 1200,
      easing: 'easeInOutQuad'
    }, '-=200')
    .add({
      targets: overlayRef.current,
      opacity: [1, 0],
      duration: 500,
      easing: 'easeInQuad'
    });

    // Cleanup: Bileşen ölürse animasyonu tamamen durdur
    return () => {
      tl.pause();
      anime.remove([logoRef.current, progressRef.current, overlayRef.current]);
    };
  }, [onComplete]);

  return (
    <div 
      ref={overlayRef} 
      className="boot-overlay"
      role="dialog" 
      aria-modal="true"
      aria-label="Sistem Yükleniyor"
    >
      <div className="boot-content">
        <div ref={logoRef} className="boot-logo" style={{ fontFamily: "'Playfair Display', serif", color: '#DEDBC8' }}>KARİYER AJANI</div>
        <div className="boot-version" style={{ color: '#C4A265' }}>v3.0 // PRISMA PROTOCOL</div>
        
        {/* Erişilebilirlik için progressbar rolü eklendi */}
        <div 
          className="boot-progress-container" 
          role="progressbar" 
          aria-valuemin="0" 
          aria-valuemax="100"
          style={{ background: 'rgba(222, 219, 200, 0.08)' }}
        >
          <div ref={progressRef} className="boot-progress-bar" style={{ background: 'linear-gradient(90deg, #C4A265, #DEDBC8)' }} />
        </div>
        
        <div className="boot-status" aria-live="polite" style={{ color: 'rgba(222, 219, 200, 0.4)' }}>Stratejik sistemler yükleniyor...</div>
      </div>
    </div>
  );
}

export default BootScreen;


