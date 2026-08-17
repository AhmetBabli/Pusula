import React from 'react';

interface TourMascotProps {
  size?: number;
  needleAngle?: number;
  look?: [number, number];
  className?: string;
}

/** Rehber maskotu — artık gerçek Pusula amblemiyle (pusula-kafa + takım
 * elbise) birebir aynı figür; sadece gözlerle ve hafif hareketle "canlanmış". */
export function TourMascot({ size = 100, needleAngle = 0, look = [0, 0], className = '' }: TourMascotProps) {
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
      <path d="M46,68 L54,68 L51,115 L49,115 Z" fill="rgb(var(--color-primary) / 0.5)" />

      {/* baş: pusula çemberi */}
      <circle cx="50" cy="40" r="25" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-primary))" strokeWidth="3" />
      {/* ince parlama */}
      <path d="M32.5 24A25 25 0 0 1 40 17" stroke="rgb(var(--color-surface))" strokeWidth="1.6" strokeLinecap="round" opacity="0.9" />

      {/* gözler */}
      <ellipse className="pusula-mascot-eye" cx="39" cy="49" rx="8" ry="9" fill="rgb(var(--color-outline-variant) / 0.12)" />
      <ellipse className="pusula-mascot-eye" cx="61" cy="49" rx="8" ry="9" fill="rgb(var(--color-outline-variant) / 0.12)" />
      <g className="pusula-mascot-pupils" style={{ transform: `translate(${look[0]}px, ${look[1]}px)` }}>
        <circle cx="39" cy="50" r="4.5" fill="rgb(var(--color-on-surface))" />
        <circle cx="61" cy="50" r="4.5" fill="rgb(var(--color-on-surface))" />
        <circle cx="37.3" cy="47.5" r="1.3" fill="rgb(var(--color-surface))" />
        <circle cx="59.3" cy="47.5" r="1.3" fill="rgb(var(--color-surface))" />
      </g>

      {/* pusula iğnesi — turdaki her adımda o yöne döner */}
      <g
        className="pusula-mascot-needle"
        style={{ transformOrigin: '50px 28px', transform: `rotate(${needleAngle}deg)` }}
      >
        <path d="M56 20L50 28L44 36L48 28L56 20Z" fill="rgb(var(--color-primary))" />
        <path d="M56 20L50 28L48 28L56 20Z" fill="rgb(var(--color-primary) / 0.5)" />
      </g>
    </svg>
  );
}
