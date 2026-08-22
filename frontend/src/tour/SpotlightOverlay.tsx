import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface SpotlightOverlayProps {
  targetSelector: string | null;
  rect: DOMRect | null;
}

const PADDING = 8;

/** Hedef elementin etrafında, box-shadow hilesiyle tek div'lik bir "spot ışığı" deliği açar.
 * rect, TourOverlay'in zaten çağırdığı useTargetRect'ten geliyor — önceden burada
 * AYNI hedefi AYNI anda ölçen ikinci, bağımsız bir 400ms polling döngüsü vardı. */
export function SpotlightOverlay({ targetSelector, rect }: SpotlightOverlayProps) {
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
