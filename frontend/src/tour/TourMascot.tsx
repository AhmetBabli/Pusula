import React from 'react';

interface TourMascotProps {
  size?: number;
  needleAngle?: number;
  className?: string;
}

/** Rehber maskotu — Pusula amblemiyle (pusula-kafa + takım elbise) birebir
 * aynı figür. Kimliği bir yüzden değil, merkezdeki büyük, gerçek bir pusula
 * iğnesi gibi çizilmiş, adım adım hedefi gösteren ibreden alıyor. */
export function TourMascot({ size = 100, needleAngle = 0, className = '' }: TourMascotProps) {
  return (
    <svg
      className={`pusula-mascot-body ${className}`}
      style={{ width: size, height: size * 1.4, filter: 'drop-shadow(0 10px 18px rgb(var(--color-primary) / 0.22))' }}
      viewBox="0 0 100 140"
      fill="none"
      aria-hidden="true"
    >
      {/* gölge */}
      <ellipse cx="50" cy="132" rx="27" ry="5" fill="rgb(var(--color-on-surface) / 0.10)" />

      {/* gövde: yaka + kravat (onaylanan amblemle aynı oranlar) */}
      <path d="M22,70 L42,62 L50,74 L58,62 L78,70 L68,125 L32,125 Z" fill="rgb(var(--color-primary))" />
      <path d="M42,62 L50,74 L58,62 L54,65.5 L50,61.5 L46,65.5 Z" fill="rgb(var(--color-surface))" />
      <path d="M46,68 L54,68 L51,115 L49,115 Z" fill="rgb(var(--color-primary-light))" />

      {/* baş: pusula çemberi */}
      <circle cx="50" cy="40" r="25" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-primary))" strokeWidth="3" />
      {/* ince parlama */}
      <path d="M32.5 24A25 25 0 0 1 40 17" stroke="rgb(var(--color-surface))" strokeWidth="1.6" strokeLinecap="round" opacity="0.9" />

      {/* pusula iğnesi — gerçek bir pusula gibi çemberin neredeyse tamamını
          kaplıyor, merkezden döner ve turdaki her adımda hedefi gösterir */}
      <g
        className="pusula-mascot-needle"
        style={{ transformOrigin: '50px 40px', transform: `rotate(${needleAngle}deg)` }}
      >
        <path d="M44,40 L56,40 L50,17 Z" fill="rgb(var(--color-primary))" />
        <path d="M44,40 L56,40 L50,63 Z" fill="rgb(var(--color-primary-light))" />
        <circle cx="50" cy="40" r="3.5" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-primary))" strokeWidth="1.5" />
      </g>
    </svg>
  );
}
