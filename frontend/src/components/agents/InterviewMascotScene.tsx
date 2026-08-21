import React from 'react';
import sceneImage from '../../assets/interview-mascot-scene.jpg';

interface InterviewMascotSceneProps {
  speaking?: boolean;
  listening?: boolean;
  thinking?: boolean;
}

// Sahnenin kendisi artık kullanıcının kendi ürettiği sabit bir görsel —
// elle çizilen SVG yerine bunu kullanıyoruz. "Canlandırma" (konuşma/dinleme/
// düşünme durumları) görselin üzerine bindirilen hafif katmanlarla yapılıyor;
// resmin kendisine dokunulmuyor. Konumlar görselin kendi oranlarına göre
// yüzde cinsinden hesaplandı (pusula başı yaklaşık sol:%40 üst:%18 genişlik:%22).
export function InterviewMascotScene({ speaking = false, listening = false, thinking = false }: InterviewMascotSceneProps) {
  return (
    <div className="relative w-full select-none" style={{ aspectRatio: '2400 / 1784' }}>
      <img
        src={sceneImage}
        alt=""
        className="absolute inset-0 w-full h-full object-contain rounded-2xl"
        draggable={false}
        aria-hidden="true"
      />

      {/* Konuşurken ya da düşünürken pusula başının etrafında yumuşak bir nabız */}
      {(speaking || thinking) && (
        <div
          className="absolute rounded-full pointer-events-none"
          style={{
            left: '39.5%', top: '18%', width: '22%', height: '29%',
            background: 'radial-gradient(circle, rgb(var(--color-primary-container) / 0.45), transparent 70%)',
            animation: `pusulaScenePulse ${thinking ? 1.6 : 1.1}s ease-in-out infinite`,
          }}
        />
      )}

      {/* Düşünürken pusula başının çevresinde dönen ince bir halka */}
      {thinking && (
        <div
          className="absolute rounded-full pointer-events-none"
          style={{
            left: '40.5%', top: '19%', width: '20%', height: '27%',
            border: '3px solid transparent',
            borderTopColor: 'rgb(var(--color-primary))',
            borderRightColor: 'rgb(var(--color-primary) / 0.4)',
            animation: 'pusulaSceneSpin 1.4s linear infinite',
          }}
        />
      )}

      {/* Dinlerken masanın yakın (izleyiciye en yakın) kenarında bir vurgu */}
      {listening && (
        <div
          className="absolute rounded-full pointer-events-none animate-pulse"
          style={{ left: '2%', right: '2%', bottom: '3%', height: '2.5%', background: 'rgb(var(--color-error) / 0.28)' }}
        />
      )}

      <style>{`
        @keyframes pusulaScenePulse {
          0%, 100% { opacity: 0.55; transform: scale(0.94); }
          50% { opacity: 1; transform: scale(1.04); }
        }
        @keyframes pusulaSceneSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
