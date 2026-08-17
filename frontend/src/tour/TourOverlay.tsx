import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import { useTour } from './TourContext';
import { SpotlightOverlay } from './SpotlightOverlay';
import { TourMascot } from './TourMascot';
import { useTargetRect } from './useTargetRect';

const MASCOT_SIZE = 124;
const GAP = 20;
const BUBBLE_WIDTH = 340;
const MARGIN = 16;

/** Hedefin konumuna göre maskot+balonun ekranda nereye yerleşeceğini hesaplar,
 * viewport dışına taşmayacak şekilde kelepçeler (clamp). */
function computePosition(rect: DOMRect | null, placement: string) {
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  if (!rect || placement === 'center') {
    return {
      left: vw / 2 - (MASCOT_SIZE + GAP + BUBBLE_WIDTH) / 2,
      top: vh / 2 - MASCOT_SIZE * 0.6,
    };
  }

  let left = rect.right + GAP;
  let top = rect.top + rect.height / 2 - MASCOT_SIZE * 0.6;

  if (placement === 'left') {
    left = rect.left - GAP - MASCOT_SIZE - BUBBLE_WIDTH;
  }

  // Sağda/solda yer yoksa, alta düş
  if (left + MASCOT_SIZE + BUBBLE_WIDTH > vw - MARGIN || left < MARGIN) {
    left = Math.min(Math.max(rect.left, MARGIN), vw - MASCOT_SIZE - BUBBLE_WIDTH - MARGIN);
    top = rect.bottom + GAP;
  }

  top = Math.min(Math.max(top, MARGIN), vh - 300);

  return { left, top };
}

export function TourOverlay() {
  const { t } = useLanguage();
  const { active, step, stepIndex, totalSteps, isFirst, isLast, next, back, skip } = useTour();
  const rect = useTargetRect(step?.target ?? null);

  if (!active || !step) return null;

  const { left, top } = computePosition(rect, step.placement);

  // İğne, gözlerin yerini alan tek "canlı" detay: gerçek bir pusula gibi
  // hedefin yönünü gösteriyor. Merkez adımlarda (hedef yok) nötr — yukarı bakar.
  let needleAngle = 0;
  if (rect) {
    const mascotCenterX = left + MASCOT_SIZE * 0.5;
    const mascotCenterY = top + MASCOT_SIZE * 0.4;
    const dx = rect.left + rect.width / 2 - mascotCenterX;
    const dy = rect.top + rect.height / 2 - mascotCenterY;
    needleAngle = (Math.atan2(dx, -dy) * 180) / Math.PI;
  }

  return (
    <>
      <SpotlightOverlay targetSelector={step.target} />

      <AnimatePresence mode="wait">
        <motion.div
          key={step.id}
          id="pusula-tour-bubble"
          className="fixed z-[101] flex items-end gap-3"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1, left, top }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          style={{ left, top }}
        >
          <TourMascot size={MASCOT_SIZE} needleAngle={needleAngle} className="shrink-0" />

          <div
            className="bg-surface-container border border-outline-variant/10 rounded-2xl shadow-2xl shadow-black/10 p-6 relative"
            style={{ width: BUBBLE_WIDTH }}
          >
            <button
              onClick={skip}
              className="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface transition-colors"
              aria-label={t('tour_v2_skip')}
            >
              <X className="w-4 h-4" />
            </button>

            <div className="text-xs font-label font-semibold text-primary mb-2.5 tracking-wide">
              {t('tour_v2_step_label')} {stepIndex + 1}/{totalSteps}
            </div>

            <h3 className="text-lg font-headline font-bold text-on-surface mb-2 pr-4">{t(step.titleKey)}</h3>
            <p className="text-[15px] font-body text-on-surface-variant leading-relaxed mb-5">{t(step.descKey)}</p>

            <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden mb-5">
              <motion.div
                className="h-full bg-primary rounded-full"
                initial={false}
                animate={{ width: `${((stepIndex + 1) / totalSteps) * 100}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>

            <div className="flex items-center justify-between">
              <button
                onClick={back}
                disabled={isFirst}
                className="text-xs font-label font-semibold text-on-surface-variant hover:text-on-surface disabled:opacity-0 disabled:pointer-events-none transition-colors"
              >
                {t('tour_back')}
              </button>
              <div className="flex items-center gap-3">
                <button
                  onClick={skip}
                  className="text-xs font-label font-semibold text-on-surface-variant hover:text-on-surface transition-colors"
                >
                  {t('tour_v2_skip')}
                </button>
                <button
                  onClick={next}
                  className="px-4 py-2 rounded-lg bg-primary-container text-white text-xs font-label font-semibold hover:bg-blue-700 active:scale-[0.97] transition-all"
                >
                  {isLast ? t('tour_v2_finish') : t('tour_next')}
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </>
  );
}
