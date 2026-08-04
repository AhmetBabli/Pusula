import React, { useState, useEffect, useRef, useCallback } from 'react';

interface Quote {
  text: string;
  author: string;
  icon: string;
}

const PHILOSOPHER_QUOTES: Quote[] = [
  { text: "Basitlik, en üst seviye sofistikeliktir.", author: "Leonardo da Vinci", icon: "🎨" },
  { text: "Fırsatı yaratan, stratejidir.", author: "Sun Tzu", icon: "⚔️" },
  { text: "Bilgi, eyleme dönüşmezse yüktür.", author: "Farabi", icon: "📜" },
  { text: "Gelecek, onu hazırlayanlara aittir.", author: "Malcolm X", icon: "🔥" },
  { text: "Zaman en kıt kaynaktır; yönetilemezse hiçbir şey yönetilemez.", author: "Peter Drucker", icon: "⏳" },
  { text: "Cesaret, direniş değil; kararlılıktır.", author: "Mustafa Kemal Atatürk", icon: "🌟" },
  { text: "Düşünceleriniz geleceğiniz olur.", author: "Mahatma Gandhi", icon: "🕊️" },
  { text: "Bilgi güçtür, ancak uygulama mükemmelliktir.", author: "Francis Bacon", icon: "🧪" },
  { text: "Her sabah iki seçeneğin var: uyumaya devam etmek ya da uyanıp hayallerinin peşinden koşmak.", author: "Konfüçyüs", icon: "🌅" },
  { text: "Tek bildiğim, hiçbir şey bilmediğimdir.", author: "Sokrates", icon: "🏛️" },
];

interface PhilosopherStripProps {
  quotes?: Quote[];
  interval?: number;
}

const PhilosopherStrip: React.FC<PhilosopherStripProps> = ({ quotes = PHILOSOPHER_QUOTES, interval = 12000 }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  // Zamanlayıcıları bellekte tutmak için useRef kullanıyoruz
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const transitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Otomatik geçişi başlatan / sıfırlayan fonksiyon
  const startAutoPlay = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    
    timerRef.current = setInterval(() => {
      changeQuote((prev) => (prev + 1) % quotes.length);
    }, interval);
  }, [quotes.length, interval]);

  // Söz değiştirme işlemini tek bir merkeze topladık
  const changeQuote = useCallback((nextIndexOrFn: number | ((prev: number) => number)) => {
    setIsTransitioning(true);
    
    // Kullanıcı hızlı hızlı tıklarsa, önceki yarım kalan animasyon süresini iptal et
    if (transitionTimeoutRef.current) clearTimeout(transitionTimeoutRef.current);
    
    transitionTimeoutRef.current = setTimeout(() => {
      setCurrentIndex(nextIndexOrFn);
      setIsTransitioning(false);
    }, 600); // CSS fade süresi
  }, []);

  // Sadece bileşen yüklendiğinde otomatik geçişi başlat
  useEffect(() => {
    if (quotes.length <= 1) return;
    startAutoPlay();
    
    // Bileşen ekrandan kalkarsa (unmount) zamanlayıcıları temizle (Memory Leak önlemi)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (transitionTimeoutRef.current) clearTimeout(transitionTimeoutRef.current);
    };
  }, [startAutoPlay, quotes.length]);

  // Noktalara tıklama (Manuel kontrol)
  const handleDotClick = (index: number) => {
    if (index === currentIndex || isTransitioning) return; // Zaten ordaysa veya animasyon sürüyorsa yoksay
    
    startAutoPlay(); // Kullanıcı tıkladığı an otomatik sayacı SIFIRLA
    changeQuote(() => index);
  };

  if (!quotes || quotes.length === 0) return null;

  const current = quotes[currentIndex];

  return (
    <div className="philosopher-strip" role="complementary" aria-label="Filozofik İlham Şeridi">
      <div className="philosopher-glow-line" />
      <div className={`philosopher-content ${isTransitioning ? 'fading' : 'visible'}`}>
        {/* Emojiler ekran okuyucuları şaşırtmasın diye aria-hidden eklendi */}
        <span className="philosopher-icon" aria-hidden="true">{current.icon}</span>
        <blockquote className="philosopher-quote">
          "{current.text}"
        </blockquote>
        <cite className="philosopher-author">— {current.author}</cite>
      </div>
      
      {/* role="tablist" ile klavye/ekran okuyucu erişilebilirliği sağlandı */}
      <div className="philosopher-dots" role="tablist">
        {quotes.map((_, i) => (
          <button 
            key={i} 
            role="tab"
            aria-selected={i === currentIndex}
            aria-label={`${i + 1}. sözü göster`}
            className={`philosopher-dot ${i === currentIndex ? 'active' : ''}`}
            onClick={() => handleDotClick(i)}
            disabled={isTransitioning} // Geçiş esnasında tıklanmayı engelle
          />
        ))}
      </div>
    </div>
  );
}

export default PhilosopherStrip;