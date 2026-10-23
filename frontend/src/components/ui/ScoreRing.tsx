import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect, useState } from 'react';

// Pusula markası ürünün içinde hiçbir yerde görsel karşılık bulmuyordu —
// eşleşme skoru dairesel olduğu için buna en doğal aday: jenerik bir
// "progress ring" yerine, kadranın çevresinde ince derece çizgileriyle
// gerçek bir pusula kadranı hissi veriyor. "Bu ilan seni ne kadar doğru
// yöne işaret ediyor" fikrini gösterge biçiminin kendisiyle taşıyor.
// Kadran anında belirmek yerine 0'dan gerçek skora doğru çizilerek dolar —
// "pusula hedefi buldu" hissi veren, tek ve kasıtlı bir hareket anı.
//
// Skor daha önce üç ekranda üç farklı biçimde gösteriliyordu (Dashboard'da
// bu kadran, İlanlar listesinde düz renkli bir kutu, İlan detayında kalın
// kenarlıklı bir daire) — paylaşılan bu bileşen tek bir görsel dili
// hepsine yayıyor.
export function ScoreRing({ score, size = 56 }: { score: number; size?: number }) {
  const pct = Math.round(score || 0);
  const tone = pct >= 65 ? '#1E7F5C' : pct >= 45 ? '#B4740E' : 'rgb(var(--color-on-surface-variant))';
  const r = 24;
  const circumference = 2 * Math.PI * r;
  const fontSize = Math.max(10, Math.round(size * 0.25));

  const progress = useMotionValue(0);
  const dashoffset = useTransform(progress, (v) => circumference - (v / 100) * circumference);
  const [displayPct, setDisplayPct] = useState(0);

  useEffect(() => {
    const controls = animate(progress, pct, {
      duration: 1.1,
      delay: 0.3,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setDisplayPct(Math.round(v)),
    });
    return () => controls.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pct]);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox="0 0 60 60" className="w-full h-full -rotate-90">
        {Array.from({ length: 24 }).map((_, i) => (
          <line
            key={i}
            x1="30" y1="1.5" x2="30" y2={i % 6 === 0 ? '5.5' : '3.5'}
            stroke="rgb(var(--color-outline-variant) / 0.3)"
            strokeWidth={i % 6 === 0 ? 1.1 : 0.6}
            transform={`rotate(${i * 15} 30 30)`}
          />
        ))}
        <circle cx="30" cy="30" r={r} fill="none" stroke="rgb(var(--color-surface-container-high))" strokeWidth="4" />
        <motion.circle
          cx="30" cy="30" r={r} fill="none" stroke={tone} strokeWidth="4" strokeLinecap="round"
          strokeDasharray={circumference}
          style={{ strokeDashoffset: dashoffset }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-bold tabular-nums font-label" style={{ color: tone, fontSize }}>{displayPct}%</span>
      </div>
    </div>
  );
}

export default ScoreRing;
