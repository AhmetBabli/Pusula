import React from 'react';

interface InterviewMascotSceneProps {
  needleAngle?: number;
  speaking?: boolean;
  listening?: boolean;
}

interface Line {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

// Masanın perspektif ızgarası: yakın kenar (izleyiciye en yakın, geniş) ile
// uzak kenar (maskotun oturduğu, dar) arasında tek noktalı perspektif.
const NEAR_Y = 615, FAR_Y = 345;
const NEAR_XL = 40, NEAR_XR = 760;
const FAR_XL = 300, FAR_XR = 500;

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const leftXAt = (t: number) => lerp(NEAR_XL, FAR_XL, t);
const rightXAt = (t: number) => lerp(NEAR_XR, FAR_XR, t);
const yAt = (t: number) => lerp(NEAR_Y, FAR_Y, t);

function buildTableGrid(): { receding: Line[]; cross: Line[] } {
  const receding: Line[] = [];
  const RECEDE_COUNT = 7;
  for (let i = 1; i < RECEDE_COUNT; i++) {
    const f = i / RECEDE_COUNT;
    receding.push({
      x1: lerp(NEAR_XL, NEAR_XR, f), y1: NEAR_Y,
      x2: lerp(FAR_XL, FAR_XR, f), y2: FAR_Y,
    });
  }
  const cross: Line[] = [];
  // Uzaklaştıkça aralar sıklaşıyor — perspektif kısalma hissi
  const depths = [0.14, 0.3, 0.46, 0.6, 0.72, 0.82, 0.9, 0.96];
  for (const t of depths) {
    cross.push({ x1: leftXAt(t), y1: yAt(t), x2: rightXAt(t), y2: yAt(t) });
  }
  return { receding, cross };
}

const TABLE_GRID = buildTableGrid();

const RIGHT_WALL_HATCH: Line[] = [0.15, 0.3, 0.45, 0.6, 0.75, 0.9].map(f => ({
  x1: lerp(560, 780, f), y1: lerp(40, 80, f),
  x2: lerp(560, 780, f) - 40, y2: lerp(40, 80, f) + 460,
}));

/** Mülakat sahnesi: Pusula masanın uzak ucunda oturuyor, sen (izleyici)
 * masanın yakın ucundasın — ayrı bir kullanıcı avatarı yok, kamera açısının
 * kendisi seni temsil ediyor. Aynı marka figürünü (pusula-kafa + takım
 * elbise) TourMascot ile paylaşıyor, ama bu sahneye özel daha büyük bir
 * gövde + masaya uzanan kollarla çizildi. */
export function InterviewMascotScene({ needleAngle = 0, speaking = false, listening = false }: InterviewMascotSceneProps) {
  return (
    <svg
      viewBox="0 0 800 640"
      className="w-full h-auto"
      style={{ filter: 'drop-shadow(0 14px 26px rgb(var(--color-primary) / 0.16))' }}
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="pusulaSceneGlow" cx="50%" cy="28%" r="65%">
          <stop offset="0%" stopColor="rgb(var(--color-primary-container))" stopOpacity="0.20" />
          <stop offset="100%" stopColor="rgb(var(--color-primary-container))" stopOpacity="0" />
        </radialGradient>
      </defs>

      <rect x="0" y="0" width="800" height="640" fill="url(#pusulaSceneGlow)" />

      {/* Sağ duvar */}
      <polygon points="560,40 780,80 780,560 560,400" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-outline-variant))" strokeWidth="1.5" opacity="0.6" />
      {RIGHT_WALL_HATCH.map((l, i) => (
        <line key={`rw-${i}`} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke="rgb(var(--color-outline-variant))" strokeWidth="1" opacity="0.45" />
      ))}

      {/* Sol duvar */}
      <polygon points="240,40 20,80 20,560 240,400" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-outline-variant))" strokeWidth="1.5" opacity="0.6" />

      {/* Duvardaki harita çerçevesi */}
      <g transform="translate(50,105) rotate(-2)">
        <rect x="0" y="0" width="140" height="170" rx="4" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-primary))" strokeWidth="3" />
        <rect x="10" y="10" width="120" height="150" fill="none" stroke="rgb(var(--color-primary))" strokeWidth="1.5" />
        <path d="M20,40 Q35,25 55,35 T95,30 Q110,45 100,60 T70,75 Q45,80 30,65 Z" fill="none" stroke="rgb(var(--color-on-surface-variant))" strokeWidth="1.2" opacity="0.7" />
        <path d="M25,95 Q45,85 65,100 T105,110 Q100,130 75,135 T35,120 Z" fill="none" stroke="rgb(var(--color-on-surface-variant))" strokeWidth="1.2" opacity="0.7" />
        <g transform="translate(25,145)">
          <circle r="10" fill="none" stroke="rgb(var(--color-primary))" strokeWidth="1" />
          <path d="M0,-9 L2,0 L0,9 L-2,0 Z" fill="rgb(var(--color-primary))" />
        </g>
      </g>

      {/* Masa yüzeyi + perspektif ızgara */}
      <polygon
        points={`${NEAR_XL},${NEAR_Y} ${NEAR_XR},${NEAR_Y} ${FAR_XR},${FAR_Y} ${FAR_XL},${FAR_Y}`}
        fill="rgb(var(--color-surface-container-highest))"
        stroke={listening ? 'rgb(var(--color-error))' : 'rgb(var(--color-primary))'}
        strokeWidth="2.5"
        style={{ transition: 'stroke 0.3s ease' }}
      />
      {TABLE_GRID.cross.map((l, i) => (
        <line key={`c-${i}`} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke="rgb(var(--color-primary))" strokeWidth="1" opacity="0.35" />
      ))}
      {TABLE_GRID.receding.map((l, i) => (
        <line key={`r-${i}`} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke="rgb(var(--color-primary))" strokeWidth="1" opacity="0.35" />
      ))}

      {/* Sandalye sırtı */}
      <rect x="305" y="150" width="190" height="200" rx="28" fill="none" stroke="rgb(var(--color-on-surface-variant))" strokeWidth="2" opacity="0.4" />

      {/* Konuşurken başın etrafında yumuşak bir nabız */}
      {speaking && (
        <circle cx="400" cy="185" r="58" fill="rgb(var(--color-primary-container))" opacity="0.25">
          <animate attributeName="r" values="56;66;56" dur="1.2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.28;0.12;0.28" dur="1.2s" repeatCount="indefinite" />
        </circle>
      )}

      {/* Maskot: masaya uzanan kollar (yuvarlak uçlu kalın çizgiler, elleri temsil eden dairelerle) */}
      <path d="M350,246 Q312,285 330,344" fill="none" stroke="rgb(var(--color-primary))" strokeWidth="26" strokeLinecap="round" />
      <path d="M450,246 Q488,285 470,344" fill="none" stroke="rgb(var(--color-primary))" strokeWidth="26" strokeLinecap="round" />
      <circle cx="330" cy="346" r="15" fill="rgb(var(--color-primary))" />
      <circle cx="470" cy="346" r="15" fill="rgb(var(--color-primary))" />

      {/* Gövde: yuvarlak omuzlu ceket, masa çizgisine kadar iniyor */}
      <path d="M336,232 Q336,220 350,222 L450,222 Q464,220 464,232 L470,300 L456,345 L344,345 L330,300 Z" fill="rgb(var(--color-primary))" />
      <path d="M380,222 L400,238 L420,222 L412,230 L400,222 L388,230 Z" fill="rgb(var(--color-surface))" />
      <path d="M393,230 L407,230 L402,338 L398,338 Z" fill="rgb(var(--color-primary-container))" />

      <circle cx="400" cy="185" r="48" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-primary))" strokeWidth="3.5" />
      <g style={{ transformOrigin: '400px 185px', transform: `rotate(${needleAngle}deg)` }}>
        <path d="M386,185 L414,185 L400,143 Z" fill="rgb(var(--color-primary))" />
        <path d="M386,185 L414,185 L400,227 Z" fill="rgb(var(--color-primary-container))" />
        <circle cx="400" cy="185" r="6" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-primary))" strokeWidth="2" />
      </g>

      {/* Not defteri + kalem */}
      <g transform="translate(340,558) rotate(-3)">
        <rect x="0" y="0" width="92" height="60" rx="4" fill="rgb(var(--color-surface))" stroke="rgb(var(--color-on-surface-variant))" strokeWidth="1.5" />
        <line x1="12" y1="16" x2="80" y2="16" stroke="rgb(var(--color-on-surface-variant))" strokeWidth="1" opacity="0.6" />
        <line x1="12" y1="28" x2="80" y2="28" stroke="rgb(var(--color-on-surface-variant))" strokeWidth="1" opacity="0.6" />
        <line x1="12" y1="40" x2="60" y2="40" stroke="rgb(var(--color-on-surface-variant))" strokeWidth="1" opacity="0.6" />
      </g>
      <g transform="translate(452,578) rotate(26)">
        <rect x="0" y="0" width="72" height="7" rx="3.5" fill="rgb(var(--color-primary))" />
        <polygon points="72,0 84,3.5 72,7" fill="rgb(var(--color-on-surface-variant))" />
      </g>
    </svg>
  );
}
