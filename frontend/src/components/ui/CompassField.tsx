import React from 'react';

// Auth ve Onboarding ekranları düz `bg-surface` üzerine oturuyordu — markanın
// tek somut motifi (pusula kadranı) daha önce sadece ScoreRing'de vardı.
// Aynı kadran dilini (24 çentik, her 6.'sı ana yön) burada dev, çok soluk bir
// arka plan filigranı olarak tekrar kullanıyoruz: yeni bir şekil icat etmek
// yerine markanın kendi imzasını büyütüp yaşatıyoruz. Üstüne, "ilan taraması"
// fikrini temsil eden yavaş bir radar süpürmesi ve birkaç yanıp sönen "sinyal"
// noktası ekleniyor — kart, pusulanın işaret ettiği hedef gibi ortada duruyor.
export function CompassField({ className = '' }: { className?: string }) {
  const ticks = Array.from({ length: 24 });
  const pings = [
    { x: '22%', y: '28%', s: 5, delay: 0 },
    { x: '78%', y: '20%', s: 4, delay: 0.8 },
    { x: '84%', y: '68%', s: 6, delay: 1.6 },
    { x: '16%', y: '72%', s: 4, delay: 2.4 },
    { x: '50%', y: '10%', s: 3, delay: 1.1 },
  ];

  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden="true">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgb(var(--color-primary)/0.08),transparent_60%)]" />

      <div className="compass-field-sweep absolute left-1/2 top-1/2 w-[860px] h-[860px] -translate-x-1/2 -translate-y-1/2" />

      <svg
        className="compass-field-ring absolute left-1/2 top-1/2 w-[860px] h-[860px] -translate-x-1/2 -translate-y-1/2"
        viewBox="0 0 200 200"
        fill="none"
      >
        <circle cx="100" cy="100" r="92" stroke="rgb(var(--color-on-surface-variant) / 0.08)" strokeWidth="1" />
        <circle cx="100" cy="100" r="70" stroke="rgb(var(--color-on-surface-variant) / 0.06)" strokeWidth="1" />
        {ticks.map((_, i) => (
          <line
            key={i}
            x1="100" y1="6" x2="100" y2={i % 6 === 0 ? '18' : '12'}
            stroke="rgb(var(--color-on-surface-variant) / 0.1)"
            strokeWidth={i % 6 === 0 ? 1.4 : 0.8}
            transform={`rotate(${i * 15} 100 100)`}
          />
        ))}
        {['N', 'E', 'S', 'W'].map((label, i) => {
          const angle = i * 90;
          const rad = (angle - 90) * (Math.PI / 180);
          const x = 100 + 80 * Math.cos(rad);
          const y = 100 + 80 * Math.sin(rad);
          return (
            <text
              key={label}
              x={x} y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="7"
              fontFamily="'JetBrains Mono', monospace"
              fill="rgb(var(--color-on-surface-variant) / 0.14)"
            >
              {label}
            </text>
          );
        })}
      </svg>

      {pings.map((p, i) => (
        <span
          key={i}
          className="compass-field-ping absolute rounded-full bg-primary"
          style={{ left: p.x, top: p.y, width: p.s, height: p.s, animationDelay: `${p.delay}s` }}
        />
      ))}

      <style>{`
        @keyframes compass-field-spin { from { transform: translate(-50%,-50%) rotate(0deg); } to { transform: translate(-50%,-50%) rotate(360deg); } }
        @keyframes compass-field-ping {
          0%, 100% { opacity: .12; transform: scale(1); }
          50% { opacity: .55; transform: scale(1.8); }
        }
        .compass-field-ring { animation: compass-field-spin 160s linear infinite; }
        .compass-field-sweep {
          animation: compass-field-spin 26s linear infinite;
          background: conic-gradient(from 0deg, rgb(var(--color-primary) / 0.16), transparent 8%, transparent 100%);
          -webkit-mask-image: radial-gradient(circle, black 50%, transparent 76%);
          mask-image: radial-gradient(circle, black 50%, transparent 76%);
          filter: blur(5px);
        }
        .compass-field-ping { animation: compass-field-ping 3.6s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .compass-field-ring, .compass-field-sweep, .compass-field-ping { animation: none; }
        }
      `}</style>
    </div>
  );
}

export default CompassField;
