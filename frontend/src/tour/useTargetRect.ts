import { useEffect, useState } from 'react';

const rectsEqual = (a: DOMRect | null, b: DOMRect | null) => {
  if (a === b) return true;
  if (!a || !b) return false;
  return a.top === b.top && a.left === b.left && a.width === b.width && a.height === b.height;
};

/** Verilen CSS seçicisine sahip elementin ekran konumunu izler; sekme
 * değişimi, kaydırma veya pencere boyutu değişince yeniden ölçer. */
export function useTargetRect(selector: string | null): DOMRect | null {
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (!selector) {
      setRect(null);
      return;
    }

    const measure = () => {
      const el = document.querySelector(selector);
      const next = el ? el.getBoundingClientRect() : null;
      // getBoundingClientRect() her çağrıda yeni bir obje döner — değerler
      // aynı olsa bile setRect(next) her 400ms'de bir gereksiz render
      // tetiklerdi. Sadece gerçekten değiştiğinde state'i güncelle.
      setRect((prev) => (rectsEqual(prev, next) ? prev : next));
    };

    const t = setTimeout(measure, 60);
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, true);
    const interval = setInterval(measure, 400);

    return () => {
      clearTimeout(t);
      clearInterval(interval);
      window.removeEventListener('resize', measure);
      window.removeEventListener('scroll', measure, true);
    };
  }, [selector]);

  return rect;
}
