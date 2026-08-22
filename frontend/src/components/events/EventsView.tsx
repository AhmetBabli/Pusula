import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, MapPin, Clock, ExternalLink, Heart, BadgeCheck, CheckCircle2, X, Search, Compass, AlertCircle } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';
import { useAgentWebSocket } from '../../hooks/useAgentWebSocket';
import { getToken } from '../../services/api';

const EVENT_TYPE_KEYS = {
  hackathon: 'events_type_hackathon',
  career_fair: 'events_type_career_fair',
  seminar: 'events_type_seminar',
  networking: 'events_type_networking',
  workshop: 'events_type_workshop',
};

// Bir durumdan sonra kullanıcının gidebileceği ileri adımlar — 'attended'/'skipped' uçlar (terminal).
const NEXT_ACTIONS = {
  found: ['interested', 'registered', 'skipped'],
  interested: ['registered', 'skipped'],
  registered: ['attended', 'skipped'],
  attended: [],
  skipped: [],
};

const STATUS_STYLE = {
  interested: { icon: Heart, tone: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20' },
  registered: { icon: BadgeCheck, tone: 'text-primary bg-primary-container/10 border-primary-container/20' },
  attended: { icon: CheckCircle2, tone: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20' },
  skipped: { icon: X, tone: 'text-on-surface-variant bg-outline-variant/5 border-outline-variant/15' },
};

function EventStatusActions({ event, onUpdateStatus, t }) {
  const [updating, setUpdating] = useState(null);
  const nextActions = NEXT_ACTIONS[event.status] || [];

  const handleClick = async (e, status) => {
    e.stopPropagation();
    if (!onUpdateStatus) return;
    setUpdating(status);
    try {
      await onUpdateStatus(event.id, status);
    } finally {
      setUpdating(null);
    }
  };

  if (event.status && STATUS_STYLE[event.status]) {
    const StatusIcon = STATUS_STYLE[event.status].icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-label font-semibold border w-fit ${STATUS_STYLE[event.status].tone}`}>
        <StatusIcon className="w-3 h-3" /> {t(`events_status_${event.status}`)}
      </span>
    );
  }

  if (!nextActions.length) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {nextActions.map((status) => (
        <button
          key={status}
          onClick={(e) => handleClick(e, status)}
          disabled={updating !== null}
          className="px-2.5 py-1 rounded-md border border-outline-variant/15 bg-surface-container-lowest hover:bg-surface-container-high text-xs font-label text-on-surface-variant hover:text-on-surface active:scale-[0.96] transition-all duration-150 disabled:opacity-50"
        >
          {updating === status ? '...' : t(`events_status_${status}`)}
        </button>
      ))}
    </div>
  );
}

function EventsView({ events, isLoading, onUpdateStatus, onEventsFound }) {
  const { t, language } = useLanguage();
  const eventTypeLabel = (eventType) => (eventType && EVENT_TYPE_KEYS[eventType] ? t(EVENT_TYPE_KEYS[eventType]) : eventType);
  const { agents, sessionId, connected } = useAgentWebSocket();
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('İstanbul');
  const search = agents.event_search;

  useEffect(() => {
    if (search.status === 'done') {
      onEventsFound?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search.status]);

  const handleSearch = async () => {
    if (!query.trim() || search.status === 'running') return;
    const token = getToken() || '';
    await fetch('/api/agents/search-events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ query, location, session_id: sessionId }),
    });
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.06 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" as const } }
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

        <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={t('events_search_query_placeholder')}
            className="bg-surface-container border border-outline-variant/15 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150 w-full sm:w-56"
          />
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={t('agents_location_placeholder')}
            className="bg-surface-container border border-outline-variant/15 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150 w-full sm:w-36"
          />
          <button
            onClick={handleSearch}
            disabled={!connected || !query.trim() || search.status === 'running'}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white text-sm font-semibold rounded-lg transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
          >
            {search.status === 'running' ? <Compass className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {search.status === 'running' ? t('events_searching') : t('events_search_button')}
          </button>
        </div>
      </motion.div>

      {search.status === 'failed' && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {search.step}
        </div>
      )}
      {search.status === 'done' && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span className="font-semibold tabular-nums">{Number(search.data?.saved_count ?? 0)}</span> {t('agents_events_found_suffix')}
        </div>
      )}

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
                    <p className="text-sm font-body text-on-surface-variant leading-relaxed line-clamp-3 mb-4 flex-1">
                      {event.description}
                    </p>
                  )}

                  {event.relevance_reason && (
                    <div className="flex items-start gap-1.5 mb-4 text-xs font-body text-on-surface-variant bg-surface-container-lowest border border-outline-variant/10 rounded-md px-3 py-2">
                      <span className="font-label font-semibold text-primary shrink-0">{t('events_relevance_label')}</span>
                      <span className="line-clamp-2">{event.relevance_reason}</span>
                    </div>
                  )}

                  <div className="mb-4">
                    <EventStatusActions event={event} onUpdateStatus={onUpdateStatus} t={t} />
                  </div>

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
