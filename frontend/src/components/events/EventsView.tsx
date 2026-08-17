import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, MapPin, Clock, ExternalLink } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';

const EVENT_TYPE_KEYS = {
  hackathon: 'events_type_hackathon',
  career_fair: 'events_type_career_fair',
  seminar: 'events_type_seminar',
  networking: 'events_type_networking',
  workshop: 'events_type_workshop',
};

function EventsView({ events, isLoading }) {
  const { t, language } = useLanguage();
  const eventTypeLabel = (eventType) => (eventType && EVENT_TYPE_KEYS[eventType] ? t(EVENT_TYPE_KEYS[eventType]) : eventType);
  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.06 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" } }
  };

  return (
    <div className="flex-1 p-6 lg:p-10 max-w-7xl mx-auto w-full flex flex-col gap-8">
      {/* Header section */}
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4"
      >
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-md bg-primary-container/15 flex items-center justify-center border border-primary-container/25">
              <Calendar className="w-4 h-4 text-primary" />
            </div>
            <h2 className="text-3xl font-headline font-bold text-on-surface tracking-tight">{t('events_title')}</h2>
          </div>
          <p className="text-sm text-on-surface-variant flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {events.length} {t('events_upcoming_suffix')}
          </p>
        </div>
      </motion.div>

      {/* List section */}
      <div className="w-full">
        {isLoading && events.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-32 bg-surface-container/50 border border-outline-variant/10 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : events.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col items-center justify-center p-16 bg-surface-container border border-outline-variant/10 rounded-lg text-center"
          >
            <div className="w-20 h-20 rounded-full bg-outline-variant/5 flex items-center justify-center mb-6">
              <Calendar className="w-10 h-10 text-on-surface-variant/50" />
            </div>
            <p className="text-lg font-headline font-medium text-on-surface mb-2">{t('events_empty_title')}</p>
            <span className="text-sm font-body text-on-surface-variant">{t('events_empty_desc')}</span>
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            <AnimatePresence>
              {events.map(event => (
                <motion.div
                  key={event.id}
                  variants={itemVariants}
                  layout
                  className="group bg-surface-container hover:bg-surface-container-high border border-outline-variant/10 hover:border-outline-variant/20 p-6 rounded-lg transition-all duration-150 flex flex-col relative overflow-hidden h-full"
                >
                  <div className="flex gap-4 items-start mb-4">
                    <div className="flex flex-col items-center justify-center min-w-[3.5rem] bg-surface-container-lowest border border-outline-variant/10 rounded-md py-2 px-3">
                      <span className="text-2xl font-bold tabular-nums text-on-surface leading-none">
                        {event.event_date ? new Date(event.event_date).getDate() : '?'}
                      </span>
                      <span className="text-[11px] font-label font-semibold text-primary mt-1">
                        {event.event_date
                          ? new Date(event.event_date).toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-US', { month: 'short' })
                          : ''
                        }
                      </span>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-lg font-headline font-medium text-on-surface leading-tight mb-2 group-hover:text-primary transition-colors duration-150">{event.title}</h4>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs font-body text-on-surface-variant">
                        {event.location && (
                          <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {event.location}</span>
                        )}
                        {event.event_type && (
                          <span className="px-2 py-0.5 rounded bg-outline-variant/5 text-on-surface/80">{eventTypeLabel(event.event_type)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {event.description && (
                    <p className="text-sm font-body text-on-surface-variant leading-relaxed line-clamp-3 mb-6 flex-1">
                      {event.description}
                    </p>
                  )}

                  {event.url && (
                    <a
                      href={event.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-auto flex items-center justify-between px-4 py-2.5 rounded-md bg-primary-container/10 text-primary hover:bg-primary-container/20 active:scale-[0.98] transition-all duration-150 text-sm font-label"
                    >
                      <span>{t('events_details_link')}</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default EventsView;
