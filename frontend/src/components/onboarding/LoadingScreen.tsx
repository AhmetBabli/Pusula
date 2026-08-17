import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useLanguage } from '../../i18n/LanguageContext';
import { LogoMark } from '../ui/Logo';

interface LoadingScreenProps {
  onComplete: () => void;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ onComplete }) => {
  const { t } = useLanguage();
  useEffect(() => {
    // 3 saniye sonra Onboarding ekranına geç
    const timer = setTimeout(() => {
      onComplete();
    }, 3000);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen bg-surface text-on-surface overflow-hidden">
      {/* Marka rengiyle yumuşak, ortalanmış bir ışıma */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgb(var(--color-primary)/0.10),transparent_60%)]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 flex flex-col items-center"
      >
        <div className="relative w-20 h-20 mb-7 flex items-center justify-center">
          <motion.div
            className="absolute inset-0 rounded-full bg-primary/10"
            animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
          />
          <div className="relative w-16 h-16 rounded-2xl bg-surface-container border border-outline-variant/10 flex items-center justify-center shadow-xl shadow-black/5">
            <motion.div
              animate={{ rotate: [0, -18, 12, -6, 0] }}
              transition={{ duration: 2.8, repeat: Infinity, repeatDelay: 0.4, ease: "easeInOut" }}
            >
              <LogoMark size={30} />
            </motion.div>
          </div>
        </div>

        <h1 className="text-3xl font-headline font-semibold tracking-tight text-on-surface mb-10">{t('app_title')}</h1>

        {/* Minimalist Loading Bar */}
        <div className="w-64 h-1 bg-surface-container-highest rounded-full overflow-hidden mb-6 relative">
          <motion.div
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 2.8, ease: "easeInOut" }}
            className="absolute top-0 left-0 h-full bg-primary rounded-full shadow-[0_0_10px_rgb(var(--color-primary)/0.5)]"
          />
        </div>

        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          className="text-sm font-label font-medium text-primary mb-16"
        >
          {t('loading_text')}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 1 }}
          className="text-xs font-body text-on-surface-variant tracking-wide opacity-80 italic"
        >
          {t('loading_quote')}
        </motion.div>
      </motion.div>
    </div>
  );
};
