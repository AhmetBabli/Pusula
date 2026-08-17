import React, { memo } from 'react';
import { LayoutDashboard, Network, ClipboardList, Calendar, FileText, Mail, Bot } from 'lucide-react';
import { motion } from 'framer-motion';
import { useLanguage } from '../../i18n/LanguageContext';

function Navigation({ activeIndex, onChange, isAuthenticated }) {
  const { t, language } = useLanguage();

  const sections = [
    { id: 0, label: t('nav_dashboard'), icon: LayoutDashboard },
    { id: 1, label: t('nav_market_analysis'), icon: Network },
    { id: 2, label: t('nav_applications'), icon: ClipboardList },
    { id: 3, label: t('nav_events'), icon: Calendar },
    { id: 4, label: t('nav_portfolio'), icon: FileText },
    { id: 5, label: t('nav_inbox'), icon: Mail },
    { id: 6, label: t('nav_agents'), icon: Bot },
  ];

  const visibleSections = isAuthenticated 
    ? sections 
    : [{ id: 0, label: t('nav_home'), icon: LayoutDashboard }];

  return (
    <nav aria-label="Ana Menü" className="w-60 flex flex-col gap-1 p-3 h-full bg-surface-container/50 border-r border-outline-variant/10 backdrop-blur-xl">
      {visibleSections.map((sec) => {
        const Icon = sec.icon;
        const isActive = activeIndex === sec.id;

        return (
          <button
            key={sec.id}
            id={`nav-tab-${sec.id}`}
            type="button"
            className={`relative flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-150 w-full text-left outline-none focus-visible:ring-2 focus-visible:ring-primary ${isActive ? 'text-primary' : 'text-on-surface-variant hover:text-on-surface hover:bg-outline-variant/5'}`}
            onClick={() => onChange(sec.id)}
            aria-label={language === 'tr' ? `${sec.label} sekmesine geç` : `Go to ${sec.label}`}
            aria-current={isActive ? 'page' : undefined}
          >
            {isActive && (
              <motion.div
                layoutId="nav-active"
                className="absolute inset-0 bg-primary/10 border border-primary/20 rounded-md"
                initial={false}
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
              />
            )}

            <Icon className="w-[18px] h-[18px] relative z-10" aria-hidden="true" />
            <span className={`text-sm font-label tracking-wide relative z-10 ${isActive ? 'font-semibold' : 'font-medium'}`}>{sec.label}</span>

            {isActive && (
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-primary rounded-r-full" />
            )}
          </button>
        );
      })}
    </nav>
  );
}

export default memo(Navigation);