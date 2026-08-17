import React from 'react';
import { motion } from 'framer-motion';
import { FileText, Radar, Mail, ArrowRight } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';
import { LogoMark } from '../ui/Logo';

interface OnboardingProps {
  onComplete: () => void;
}

export const Onboarding: React.FC<OnboardingProps> = ({ onComplete }) => {
  const { t } = useLanguage();
  const features = [
    {
      icon: FileText,
      title: t('onboarding_feature_cv_title'),
      desc: t('onboarding_feature_cv_desc')
    },
    {
      icon: Radar,
      title: t('onboarding_feature_radar_title'),
      desc: t('onboarding_feature_radar_desc')
    },
    {
      icon: Mail,
      title: t('onboarding_feature_inbox_title'),
      desc: t('onboarding_feature_inbox_desc')
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface text-on-surface px-6 py-12 relative overflow-hidden">
      <div className="relative z-10 max-w-5xl w-full flex flex-col items-center text-center">
        
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="flex items-center gap-3 mb-8"
        >
          <LogoMark size={44} />
          <span className="text-2xl font-headline font-bold text-on-surface tracking-tight">{t('app_title')}</span>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: -10 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-xs font-label font-semibold text-primary mb-4 border border-primary-container/30 px-4 py-1.5 rounded-full bg-primary-container/10"
        >
          {t('onboarding_how_it_works')}
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-4xl md:text-5xl lg:text-6xl font-headline font-semibold tracking-tight text-on-surface mb-6 leading-tight"
        >
          {t('onboarding_heading_1')} <br />
          <span className="text-on-surface-variant">{t('onboarding_heading_2')}</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="text-on-surface-variant max-w-2xl text-lg font-body mb-16 leading-relaxed"
        >
          {t('onboarding_intro')}
        </motion.p>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-16"
        >
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <motion.div key={i} variants={itemVariants} className="group bg-surface-container border border-outline-variant/10 p-8 rounded-2xl text-left transition-all duration-500 hover:-translate-y-2 hover:border-outline-variant/20 hover:shadow-xl hover:bg-surface-container-highest cursor-default">
                <div className="w-12 h-12 rounded-xl bg-primary-container/10 border border-primary-container/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-headline font-medium text-on-surface mb-3">{f.title}</h3>
                <p className="text-sm text-on-surface-variant font-body leading-relaxed group-hover:text-on-surface/90 transition-colors">
                  {f.desc}
                </p>
              </motion.div>
            );
          })}
        </motion.div>

        <motion.button 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1, duration: 0.5 }}
          onClick={onComplete}
          className="group flex items-center gap-3 px-8 py-4 bg-primary-container hover:bg-blue-700 text-white text-base font-label rounded-xl transition-all duration-300 shadow-lg shadow-primary-container/20"
        >
          {t('onboarding_start_button')}
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </motion.button>
      </div>
    </div>
  );
};
