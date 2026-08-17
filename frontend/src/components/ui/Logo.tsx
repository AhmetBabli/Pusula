import React from 'react';

interface LogoProps {
  size?: number;
  className?: string;
}

/** Pusula marka işareti: çember + iki tonlu pusula iğnesi. */
export function LogoMark({ size = 28, className = '' }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <circle cx="14" cy="14" r="12" stroke="rgb(var(--color-primary))" strokeWidth="2" />
      <path d="M18 9L14 14L9 18L13 13L18 9Z" fill="rgb(var(--color-primary))" />
      <path d="M18 9L14 14L13 13L18 9Z" fill="rgb(var(--color-primary) / 0.5)" />
      {/* İnce cam/metal parlaması — düz tasarımı bozmadan hafif bir cila hissi verir */}
      <path d="M3.6 8A12 12 0 0 1 8 3.6" stroke="rgb(var(--color-surface))" strokeWidth="1.3" strokeLinecap="round" opacity="0.7" />
    </svg>
  );
}

interface LogoLockupProps extends LogoProps {
  wordmark: string;
  tagline?: string;
}

/** Marka işareti + isim (+ opsiyonel etiket) birlikte — header/sidebar için hazır blok. */
export function LogoLockup({ wordmark, tagline, size = 28, className = '' }: LogoLockupProps) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <LogoMark size={size} />
      <div className="flex flex-col leading-none">
        <span className="text-base font-headline font-bold text-on-surface tracking-tight">{wordmark}</span>
        {tagline && (
          <span className="text-[11px] text-on-surface-variant font-medium mt-0.5">{tagline}</span>
        )}
      </div>
    </div>
  );
}

export default LogoMark;
