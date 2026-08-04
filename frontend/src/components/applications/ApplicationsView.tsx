import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ClipboardList, CheckCircle, XCircle, Clock, Send, FileText, ArrowRight, Activity, Mail, AlertTriangle, ExternalLink, RotateCcw } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';

function ApplicationsView({ applications, isLoading, onApprove, onSubmit }) {
  const { t, language } = useLanguage();

  const EMAIL_SOURCE_LABEL = {
    job_posting: { text: t('applications_source_job_posting'), tone: 'text-emerald-500' },
    web_search: { text: t('applications_source_web_search'), tone: 'text-yellow-500' },
    manual: { text: t('applications_source_manual'), tone: 'text-on-surface-variant' },
  };

  const STATUS_FLOW = [
    { key: 'draft', label: t('applications_status_draft'), icon: FileText },
    { key: 'awaiting_approval', label: t('applications_status_awaiting'), icon: Clock },
    { key: 'approved', label: t('applications_status_approved'), icon: CheckCircle },
    { key: 'submitted', label: t('applications_status_submitted'), icon: Send },
  ];

  const [selectedApp, setSelectedApp] = useState(null);
  const [filter, setFilter] = useState('');
  const [emailDrafts, setEmailDrafts] = useState({});

  const emailFor = (app) => emailDrafts[app.id] ?? app.contact_email ?? '';

  const filtered = applications.filter(app => {
    if (!filter) return true;
    return app.status === filter;
  });

  const getStatusIndex = (status) => STATUS_FLOW.findIndex(s => s.key === status);

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
              <ClipboardList className="w-4 h-4 text-primary" />
            </div>
            <h2 className="text-3xl font-headline font-bold text-on-surface tracking-tight">{t('applications_title')}</h2>
          </div>
          <p className="text-sm font-mono text-on-surface-variant tracking-wider uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {applications.length} {t('applications_count_suffix')}
          </p>
        </div>

        <div className="flex items-center bg-surface-container border border-outline-variant/10 p-1 rounded-md">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-transparent border-none text-sm text-on-surface font-label focus:ring-0 cursor-pointer pr-8 pl-4 py-2"
          >
            <option value="" className="bg-surface-container">{t('applications_filter_all')}</option>
            {STATUS_FLOW.map(s => (
              <option key={s.key} value={s.key} className="bg-surface-container">{s.label}</option>
            ))}
          </select>
        </div>
      </motion.div>

      {/* List section */}
      <div className="w-full">
        {isLoading && applications.length === 0 ? (
          <div className="space-y-3">
            {[1,2,3].map(i => (
              <div key={i} className="h-32 bg-surface-container/50 border border-outline-variant/10 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col items-center justify-center p-16 bg-surface-container border border-outline-variant/10 rounded-lg text-center"
          >
            <div className="w-20 h-20 rounded-full bg-outline-variant/5 flex items-center justify-center mb-6">
              <ClipboardList className="w-10 h-10 text-on-surface-variant/50" />
            </div>
            <p className="text-lg font-headline font-medium text-on-surface mb-2">{t('applications_empty_title')}</p>
            <span className="text-sm font-body text-on-surface-variant">{t('applications_empty_desc')}</span>
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-3"
          >
            <AnimatePresence>
              {filtered.map(app => {
                const currentStep = getStatusIndex(app.status);
                return (
                  <motion.div
                    key={app.id}
                    variants={itemVariants}
                    layout
                    className="bg-surface-container hover:bg-surface-container-high border border-outline-variant/10 hover:border-outline-variant/20 p-6 rounded-lg transition-all duration-150 flex flex-col gap-6"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-xl font-headline font-medium text-on-surface mb-1">{app.job?.title || t('applications_untitled_job')}</h4>
                        <span className="text-sm font-body text-on-surface-variant">{app.job?.company}</span>
                      </div>

                      <div className="flex gap-2">
                        {app.status === 'awaiting_approval' && (
                          <>
                            <button
                              className="p-2 rounded-md bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 active:scale-[0.94] transition-all duration-150 border border-emerald-500/20"
                              onClick={() => onApprove(app.id, true, emailFor(app))}
                              title={t('applications_approve')}
                            >
                              <CheckCircle className="w-5 h-5" />
                            </button>
                            <button
                              className="p-2 rounded-md bg-red-500/10 text-red-500 hover:bg-red-500/20 active:scale-[0.94] transition-all duration-150 border border-red-500/20"
                              onClick={() => onApprove(app.id, false)}
                              title={t('applications_reject')}
                            >
                              <XCircle className="w-5 h-5" />
                            </button>
                          </>
                        )}
                        {app.status === 'approved' && (
                          <button
                            className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary-container hover:bg-blue-700 active:scale-[0.97] text-white text-sm font-label transition-all duration-150"
                            onClick={() => onSubmit(app.id)}
                          >
                            {app.send_status === 'failed' ? <RotateCcw className="w-4 h-4" /> : <Send className="w-4 h-4" />}
                            {app.send_status === 'failed' ? t('applications_retry') : t('applications_send')}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* E-posta ile onaylı gönderim: onay öncesi düzenlenebilir alan */}
                    {app.status === 'awaiting_approval' && (
                      <div className="flex flex-col gap-1.5">
                        <label className="flex items-center gap-1.5 text-xs font-label text-on-surface-variant uppercase tracking-wider">
                          <Mail className="w-3.5 h-3.5" /> {t('applications_contact_email_label')}
                        </label>
                        <input
                          type="email"
                          value={emailFor(app)}
                          onChange={(e) => setEmailDrafts((prev) => ({ ...prev, [app.id]: e.target.value }))}
                          placeholder={t('applications_contact_email_placeholder')}
                          className="bg-surface-container-lowest border border-outline-variant/15 rounded-md px-3 py-2 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors"
                        />
                        {app.contact_email_source && EMAIL_SOURCE_LABEL[app.contact_email_source] && (
                          <span className={`text-xs font-label flex items-center gap-1 ${EMAIL_SOURCE_LABEL[app.contact_email_source].tone}`}>
                            {app.contact_email_source === 'web_search' && <AlertTriangle className="w-3.5 h-3.5" />}
                            {EMAIL_SOURCE_LABEL[app.contact_email_source].text}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Onaylandı: hedef e-posta veya kopyala-yapıştır bilgisi + gönderim hatası */}
                    {app.status === 'approved' && (
                      <div className="text-sm font-body text-on-surface-variant flex items-center gap-1.5">
                        <Mail className="w-3.5 h-3.5 shrink-0" />
                        {app.contact_email ? (
                          <span>{t('applications_will_send_to')} <span className="text-on-surface font-medium">{app.contact_email}</span></span>
                        ) : (
                          <span>{t('applications_no_email_hint')}</span>
                        )}
                      </div>
                    )}
                    {app.status === 'approved' && app.send_status === 'failed' && (
                      <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm">
                        <AlertTriangle className="w-4 h-4 shrink-0" />
                        {app.send_error || t('applications_send_failed_fallback')}
                      </div>
                    )}

                    {/* Gönderildi: gerçek e-posta sonucu ya da kopyala-yapıştır bilgisi */}
                    {app.status === 'submitted' && app.send_status === 'sent' && (
                      <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm">
                        <CheckCircle className="w-4 h-4 shrink-0" />
                        {language === 'tr' ? `${app.contact_email} adresine gönderildi.` : `Sent to ${app.contact_email}.`}
                      </div>
                    )}
                    {app.status === 'submitted' && app.send_status === 'not_applicable' && (
                      <div className="flex flex-col gap-2 p-4 rounded-md bg-surface-container-lowest border border-outline-variant/10">
                        <span className="text-sm font-body text-on-surface-variant">
                          {t('applications_manual_fallback_desc')}
                        </span>
                        {app.job?.source_url && (
                          <a
                            href={app.job.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-sm font-label text-primary hover:underline underline-offset-2 w-fit"
                          >
                            {t('applications_go_to_listing')} <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                    )}

                    {/* Timeline */}
                    <div className="flex items-center w-full relative">
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-px bg-outline-variant/10" />
                      <div className="flex justify-between w-full relative z-10">
                        {STATUS_FLOW.map((step, idx) => {
                          const StepIcon = step.icon;
                          const isActive = idx <= currentStep;
                          const isCurrent = idx === currentStep;
                          return (
                            <div key={step.key} className="flex flex-col items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-150 ${isActive ? 'bg-primary border-primary text-white' : 'bg-surface-container border-outline-variant/15 text-on-surface-variant'}`}>
                                <StepIcon className={`w-4 h-4 ${isCurrent ? 'animate-pulse' : ''}`} />
                              </div>
                              <div className={`text-[10px] font-label tracking-wider uppercase ${isActive ? 'text-primary' : 'text-on-surface-variant/50'}`}>
                                {step.label}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {app.cover_letter_preview && (
                      <div className="flex items-start gap-3 p-4 rounded-md bg-surface-container-lowest border border-outline-variant/10 mt-2">
                        <FileText className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                        <p className="text-sm font-body text-on-surface-variant leading-relaxed italic">
                          "{app.cover_letter_preview}"
                        </p>
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default ApplicationsView;
