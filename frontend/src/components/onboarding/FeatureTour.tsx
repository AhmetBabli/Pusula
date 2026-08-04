import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Network, ClipboardList, Calendar, FileText, Mail, Bot,
  ArrowRight, ArrowLeft, ShieldCheck,
} from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';

interface FeatureTourProps {
  onComplete: () => void;
}

const SECTION_ICONS = [LayoutDashboard, Network, ClipboardList, Calendar, FileText, Mail, Bot];

export const FeatureTour: React.FC<FeatureTourProps> = ({ onComplete }) => {
  const { t } = useLanguage();
  const [step, setStep] = useState(0);

  const SECTIONS = [
    { icon: SECTION_ICONS[0], title: t('tour_section_1_title'), desc: t('tour_section_1_desc') },
    { icon: SECTION_ICONS[1], title: t('tour_section_2_title'), desc: t('tour_section_2_desc') },
    { icon: SECTION_ICONS[2], title: t('tour_section_3_title'), desc: t('tour_section_3_desc'), highlight: t('tour_section_3_highlight') },
    { icon: SECTION_ICONS[3], title: t('tour_section_4_title'), desc: t('tour_section_4_desc') },
    { icon: SECTION_ICONS[4], title: t('tour_section_5_title'), desc: t('tour_section_5_desc') },
    { icon: SECTION_ICONS[5], title: t('tour_section_6_title'), desc: t('tour_section_6_desc') },
    { icon: SECTION_ICONS[6], title: t('tour_section_7_title'), desc: t('tour_section_7_desc') },
  ];

  const isLast = step === SECTIONS.length - 1;
  const section = SECTIONS[step];
  const Icon = section.icon;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface text-on-surface px-6">
      <div className="w-full max-w-lg">
        <div className="flex items-center justify-center gap-2 mb-8">
          {SECTIONS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i === step ? 'w-8 bg-primary' : i < step ? 'w-4 bg-primary/40' : 'w-4 bg-outline-variant/15'
              }`}
            />
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            transition={{ duration: 0.25 }}
            className="bg-surface-container border border-outline-variant/10 rounded-2xl p-8 md:p-10 text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-primary-container/10 border border-primary-container/20 flex items-center justify-center mx-auto mb-6">
              <Icon className="w-8 h-8 text-primary" />
            </div>
            <div className="text-xs font-label text-on-surface-variant uppercase tracking-[0.2em] mb-2">
              {step + 1} / {SECTIONS.length}
            </div>
            <h2 className="text-2xl font-headline font-semibold text-on-surface mb-4">{section.title}</h2>
            <p className="text-base font-body text-on-surface-variant leading-relaxed">{section.desc}</p>

            {section.highlight && (
              <div className="mt-5 flex items-start gap-3 p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-left">
                <ShieldCheck className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                <p className="text-sm font-body text-on-surface-variant leading-relaxed">{section.highlight}</p>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="flex items-center justify-between mt-8">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-label text-on-surface-variant hover:text-on-surface transition-colors disabled:opacity-0 disabled:pointer-events-none"
          >
            <ArrowLeft className="w-4 h-4" /> {t('tour_back')}
          </button>
          <button
            type="button"
            onClick={() => (isLast ? onComplete() : setStep((s) => s + 1))}
            className="flex items-center gap-2 px-6 py-3 bg-primary-container hover:bg-blue-700 text-white text-sm font-label rounded-xl transition-colors"
          >
            {isLast ? t('tour_continue') : t('tour_next')} <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
