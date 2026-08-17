import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface SpotlightOverlayProps {
  targetSelector: string | null;
}

const PADDING = 8;

/** Hedef elementin etrafında, box-shadow hilesiyle tek div'lik bir "spot ışığı" deliği açar. */
export function SpotlightOverlay({ targetSelector }: SpotlightOverlayProps) {
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (!targetSelector) {
      setRect(null);
      return;
    }

    const measure = () => {
      const el = document.querySelector(targetSelector);
      setRect(el ? el.getBoundingClientRect() : null);
    };

    // İlk ölçüm bir tık gecikmeli — sekme geçişinden hemen sonra hedef DOM'a
    // henüz gelmemiş olabilir.
    const t = setTimeout(measure, 60);
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, true);
    const interval = setInterval(measure, 400); // layout kaymalarını (animasyonlar vb.) yakalamak için

    return () => {
      clearTimeout(t);
      clearInterval(interval);
      window.removeEventListener('resize', measure);
      window.removeEventListener('scroll', measure, true);
    };
  }, [targetSelector]);

  return (
    <div className="fixed inset-0 z-[100] pointer-events-none">
      <AnimatePresence>
        {!targetSelector && (
          <motion.div
            key="dim"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-surface-dim/50"
          />
        )}
        {rect && (
          <motion.div
            key="hole"
            className="absolute rounded-xl"
            initial={false}
            animate={{
              top: rect.top - PADDING,
              left: rect.left - PADDING,
              width: rect.width + PADDING * 2,
              height: rect.height + PADDING * 2,
              boxShadow: '0 0 0 9999px rgb(var(--color-surface-dim) / 0.55)',
            }}
            transition={{ type: 'spring', stiffness: 260, damping: 28 }}
            style={{ outline: '2px solid rgb(var(--color-primary))', outlineOffset: 2 }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
