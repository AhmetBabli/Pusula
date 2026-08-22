import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, MailOpen, Briefcase, Calendar, AlertCircle, RefreshCw, ChevronDown, Send, CheckCircle2 } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';

function InboxView({ items, isLoading, onSync, onMarkRead, onConvertToApplication }) {
  const { t, language } = useLanguage();
  const [expandedId, setExpandedId] = useState(null);
  const [convertingId, setConvertingId] = useState(null);
  const [convertError, setConvertError] = useState(null);

  const toggleExpand = (item) => {
    const opening = expandedId !== item.id;
    setExpandedId(opening ? item.id : null);
    if (opening && !item.is_read) {
      onMarkRead?.(item.id);
    }
  };

  const handleConvert = async (e, item) => {
    e.stopPropagation();
    setConvertError(null);
    setConvertingId(item.id);
    try {
      await onConvertToApplication?.(item.id);
    } catch (err) {
      setConvertError(item.id);
    } finally {
      setConvertingId(null);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'job': return <Briefcase className="w-5 h-5" />;
      case 'event': return <Calendar className="w-5 h-5" />;
      case 'hackathon': return <AlertCircle className="w-5 h-5" />;
      default: return <Mail className="w-5 h-5" />;
    }
  };

  const getTypeLabel = (type) => {
    const labels = {
      job: t('inbox_type_job'),
      event: t('inbox_type_event'),
      hackathon: t('inbox_type_hackathon'),
      career_fair: t('inbox_type_career_fair'),
      course: t('inbox_type_course'),
      update: t('inbox_type_update'),
    };
    return labels[type] || type?.toUpperCase();
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
              <Mail className="w-4 h-4 text-primary" />
            </div>
            <h2 className="text-3xl font-headline font-bold text-on-surface tracking-tight">{t('inbox_title')}</h2>
          </div>
          <p className="text-sm text-on-surface-variant flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {items.length} {t('inbox_opportunities_suffix')}
          </p>
        </div>

        <button
          onClick={onSync}
          disabled={isLoading}
          className="flex items-center gap-2 px-6 py-2.5 bg-surface-container hover:bg-surface-container-high active:scale-[0.98] border border-outline-variant/15 text-on-surface text-sm font-label rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed group"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-primary' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
          {isLoading ? t('inbox_syncing') : t('inbox_sync')}
        </button>
      </motion.div>

      {/* List section */}
      <div className="w-full">
        {isLoading && items.length === 0 ? (
          <div className="space-y-3">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-28 bg-surface-container/50 border border-outline-variant/10 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col items-center justify-center p-16 bg-surface-container border border-outline-variant/10 rounded-lg text-center"
          >
            <div className="w-20 h-20 rounded-full bg-outline-variant/5 flex items-center justify-center mb-6">
              <MailOpen className="w-10 h-10 text-on-surface-variant/50" />
            </div>
            <p className="text-lg font-headline font-medium text-on-surface mb-2">{t('inbox_empty_title')}</p>
            <span className="text-sm font-body text-on-surface-variant">{t('inbox_empty_desc')}</span>
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-3"
          >
            <AnimatePresence>
              {items.map(item => {
                const isExpanded = expandedId === item.id;
                return (
                <motion.div
                  key={item.id}
                  variants={itemVariants}
                  layout
                  onClick={() => toggleExpand(item)}
                  className={`group bg-surface-container hover:bg-surface-container-high border ${!item.is_read ? 'border-primary/30' : 'border-outline-variant/10'} hover:border-outline-variant/20 p-5 rounded-lg transition-all duration-150 flex flex-col gap-4 cursor-pointer`}
                >
                  <div className="flex flex-col md:flex-row gap-4 md:items-center">
                    <div className={`w-11 h-11 rounded-md flex items-center justify-center shrink-0 ${!item.is_read ? 'bg-primary border border-primary text-white' : 'bg-surface-container-lowest border border-outline-variant/10 text-on-surface-variant'}`}>
                      {getIcon(item.item_type)}
                    </div>

                    <div className="flex-1 flex flex-col gap-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <h4 className={`text-base font-headline font-medium truncate ${!item.is_read ? 'text-on-surface' : 'text-on-surface/80'}`}>
                          {item.title}
                        </h4>
                        <span className="px-2 py-0.5 rounded bg-outline-variant/5 text-[10px] font-label text-on-surface-variant tracking-wider shrink-0">
                          {getTypeLabel(item.item_type)}
                        </span>
                      </div>

                      <div className="text-sm font-body text-on-surface-variant truncate">
                        <span className="font-medium text-on-surface/60 mr-2">{item.sender}</span>
                        {item.body_summary}
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0 self-start md:self-center">
                      <span className="text-xs tabular-nums text-on-surface-variant/60">
                        {item.received_at ? new Date(item.received_at).toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-US', { day: 'numeric', month: 'short' }) : ''}
                      </span>
                      <ChevronDown className={`w-4 h-4 text-on-surface-variant/50 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
                    </div>
                  </div>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div
                          className="pt-4 mt-1 border-t border-outline-variant/10 flex flex-col gap-4"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <p className="text-sm font-body text-on-surface-variant leading-relaxed">
                            {item.body_summary || item.content_original}
                          </p>

                          {item.content_original && item.content_original !== item.body_summary && (
                            <details className="group">
                              <summary className="flex items-center gap-1.5 text-xs font-label text-on-surface-variant/70 hover:text-on-surface-variant cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
                                <ChevronDown className="w-3.5 h-3.5 transition-transform duration-200 group-open:rotate-180" />
                                {t('inbox_view_full_email')}
                              </summary>
                              <div className="mt-3 max-h-64 overflow-y-auto whitespace-pre-wrap text-xs font-body text-on-surface-variant/80 leading-relaxed bg-surface-container-lowest border border-outline-variant/10 rounded-md p-4">
                                {item.content_original.slice(0, 5000)}
                              </div>
                            </details>
                          )}

                          {item.item_type === 'job' && (
                            <div className="flex items-center gap-3">
                              {item.is_applied ? (
                                <span className="inline-flex items-center gap-1.5 text-sm font-label text-emerald-500">
                                  <CheckCircle2 className="w-4 h-4" /> {t('inbox_already_tracked')}
                                </span>
                              ) : (
                                <button
                                  onClick={(e) => handleConvert(e, item)}
                                  disabled={convertingId === item.id}
                                  className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary-container hover:bg-blue-700 active:scale-[0.97] text-white text-sm font-label transition-all duration-150 disabled:opacity-50"
                                >
                                  <Send className="w-4 h-4" />
                                  {convertingId === item.id ? t('inbox_converting') : t('inbox_convert_to_application')}
                                </button>
                              )}
                              {convertError === item.id && (
                                <span className="text-xs text-error">{t('inbox_convert_error')}</span>
                              )}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );})}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default InboxView;
