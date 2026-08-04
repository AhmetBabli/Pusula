import React, { memo } from 'react';

const Sticker = ({ 
  emoji, 
  top, 
  left, 
  right, 
  bottom, 
  speed = '3', 
  size = '2rem',
  ariaLabel = 'sticker' // Erişilebilirlik için eklendi
}) => {
  // Koşullu (conditional) objeleri spread operatörüyle çok daha temiz birleştiriyoruz
  const style = { 
    fontSize: size,
    position: 'absolute', // Güvenlik katmanı: Koordinatların kesin çalışmasını sağlar
    ...(top && { top }),
    ...(left && { left }),
    ...(right && { right }),
    ...(bottom && { bottom }),
  };

  return (
    <span
      className="sticker"
      data-scroll
      data-scroll-speed={speed}
      style={style}
      // Ekran okuyucuların emojiyi doğru algılaması/göz ardı etmesi için standartlar:
      role="img"
      aria-label={ariaLabel}
      aria-hidden={ariaLabel === 'sticker'} 
    >
      {emoji}
    </span>
  );
};

// React.memo ile sarmalayarak, proplar değişmediği sürece 
// bileşenin gereksiz yere tekrar render edilmesini (çizilmesini) engelliyoruz.
export default memo(Sticker);