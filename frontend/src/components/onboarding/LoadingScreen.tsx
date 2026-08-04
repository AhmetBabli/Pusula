import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useLanguage } from '../../i18n/LanguageContext';

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
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface text-on-surface">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 flex flex-col items-center"
      >
        <div className="w-16 h-16 rounded-2xl bg-surface-container-highest border border-outline-variant/10 flex items-center justify-center mb-6 shadow-xl shadow-black/10">
          <div className="w-8 h-8 rounded bg-primary animate-pulse" />
        </div>
        
        <h1 className="text-3xl font-headline font-semibold tracking-tight text-on-surface mb-10">{t('app_title')}</h1>
        
        {/* Minimalist Loading Bar */}
        <div className="w-64 h-1 bg-surface-container-highest rounded-full overflow-hidden mb-6 relative">
          <motion.div 
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 2.8, ease: "easeInOut" }}
            className="absolute top-0 left-0 h-full bg-primary rounded-full shadow-[0_0_10px_rgba(37,99,235,0.5)]" 
          />
        </div>

        <motion.div 
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          className="text-xs font-label text-primary uppercase tracking-[0.2em] mb-16"
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
