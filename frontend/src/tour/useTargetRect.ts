import { useEffect, useState } from 'react';

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
      setRect(el ? el.getBoundingClientRect() : null);
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
