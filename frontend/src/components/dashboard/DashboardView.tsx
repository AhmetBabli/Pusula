import React from 'react';
import {
  ClipboardList, Star, ArrowRight, ChevronRight,
  Zap, Shield, Send, CheckCircle2,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useLanguage } from '../../i18n/LanguageContext';

function ScoreRing({ score }: { score: number }) {
  const pct = Math.round(score || 0);
  const tone = pct >= 65 ? '#1E7F5C' : pct >= 45 ? '#B4740E' : 'rgb(var(--color-on-surface-variant))';
  return (
    <div
      className="relative w-14 h-14 rounded-full flex items-center justify-center shrink-0"
      style={{ background: `conic-gradient(${tone} ${pct * 3.6}deg, rgb(var(--color-surface-container-high)) 0deg)` }}
    >
      <div className="absolute inset-[3px] rounded-full bg-surface-container-lowest flex items-center justify-center">
        <span className="text-sm font-bold tabular-nums" style={{ color: tone }}>{pct}%</span>
      </div>
    </div>
  );
}

function DashboardView({
  stats,
  isLoading,
  gmailConnectedEmail,
  onDeepScan,
  onOpenGmail,
  onOpenOutreach,
  onOpenJobs,
  onOpenApplications,
}) {
  const { t } = useLanguage();

  const topMatches = (stats?.top_matches || []).slice(0, 4);
  const hero = topMatches[0];
  const restMatches = topMatches.slice(1);

  const statRows = [
    { label: t('dashboard_stat_total_jobs'), value: stats?.total_jobs || 0, onClick: onOpenJobs },
    { label: t('dashboard_stat_new_jobs'), value: stats?.new_jobs || 0 },
    { label: t('dashboard_stat_applications'), value: stats?.total_applications || 0, onClick: onOpenApplications },
    { label: t('dashboard_stat_pending'), value: stats?.pending_approvals || 0, onClick: onOpenApplications, warn: (stats?.pending_approvals || 0) > 0 },
  ];

  return (
    <div className="w-full max-w-[1160px] mx-auto">
      <motion.header initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="mb-7">
        <h2 className="font-headline text-[26px] md:text-[28px] text-on-surface mb-1.5 font-bold tracking-tight text-balance">{t('dashboard_title')}</h2>
        <p className="font-body text-[13.5px] text-on-surface-variant">{t('dashboard_subtitle')}</p>
      </motion.header>

      {/* Odak kartı + kompakt istatistik kartı */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.05 }}
        className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-4 mb-4">

        {hero ? (
          <div className="bg-surface-container border border-outline-variant/10 rounded-2xl p-6 flex flex-col gap-4">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary w-fit">
              <Star className="w-3.5 h-3.5" /> {t('dashboard_top_matches')}
            </span>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-headline font-semibold text-on-surface leading-snug text-balance">{hero.title}</h3>
                <p className="text-[13px] text-on-surface-variant mt-0.5">{hero.company}</p>
              </div>
              <ScoreRing score={hero.match_score} />
            </div>
            <div className="flex gap-3 mt-1">
              <button
                onClick={onOpenJobs}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary-container hover:bg-primary text-white text-sm font-semibold rounded-lg transition-colors duration-150"
              >
                {t('dashboard_prepare_application')} <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={onOpenJobs}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-surface-container-lowest hover:bg-surface-container-high border border-outline-variant/15 text-on-surface text-sm font-medium rounded-lg transition-colors duration-150"
              >
                {t('dashboard_see_details')}
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-surface-container border border-outline-variant/10 rounded-2xl p-6 flex items-center justify-center text-sm text-on-surface-variant">
            {t('dashboard_no_matches_yet')}
          </div>
        )}

        <div className="bg-surface-container border border-outline-variant/10 rounded-2xl overflow-hidden">
          {statRows.map((row, idx) => (
            <button
              key={idx}
              onClick={row.onClick}
              disabled={!row.onClick}
              className={`w-full flex items-center justify-between px-5 py-3.5 text-left ${idx !== statRows.length - 1 ? 'border-b border-outline-variant/10' : ''} ${row.onClick ? 'hover:bg-surface-container-high cursor-pointer' : 'cursor-default'} transition-colors duration-150`}
            >
              <span className="text-[13px] text-on-surface-variant font-medium">{row.label}</span>
              <span className={`text-lg font-semibold tabular-nums ${row.warn ? 'text-[#B4740E]' : 'text-on-surface'}`}>{row.value}</span>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Sakin hızlı-aksiyon çubuğu */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.1 }}
        className="flex flex-wrap items-center gap-2 mb-8">
        <button
          onClick={onDeepScan} disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary-container hover:bg-primary active:scale-[0.98] text-white text-sm font-semibold rounded-lg transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface"
        >
          <Zap className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? t('dashboard_scanning') : t('dashboard_scan_jobs')}
        </button>
        <button
          onClick={onOpenGmail}
          title={gmailConnectedEmail || undefined}
          className={`flex items-center gap-2 px-4 py-2.5 active:scale-[0.98] text-sm font-medium rounded-lg transition-all duration-150 ${
            gmailConnectedEmail
              ? 'text-[#1E7F5C]'
              : 'bg-surface-container-lowest hover:bg-surface-container-high border border-outline-variant/15 text-on-surface'
          }`}
        >
          {gmailConnectedEmail ? <CheckCircle2 className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
          {gmailConnectedEmail ? `${t('dashboard_gmail_connected')}: ${gmailConnectedEmail}` : t('dashboard_connect_gmail')}
        </button>
        <button
          onClick={onOpenOutreach}
          className="flex items-center gap-2 px-4 py-2.5 bg-surface-container-lowest hover:bg-surface-container-high active:scale-[0.98] border border-outline-variant/15 text-on-surface text-sm font-medium rounded-lg transition-all duration-150"
        >
          <Send className="w-4 h-4" /> {t('dashboard_cold_email')}
        </button>
      </motion.div>

      {restMatches.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.15 }}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[15px] font-headline font-semibold text-on-surface">{t('dashboard_other_matches')}</h3>
            <button onClick={onOpenJobs} className="flex items-center gap-1 text-[13px] font-medium text-primary hover:underline underline-offset-2">
              {t('dashboard_see_all')} <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="bg-surface-container border border-outline-variant/10 rounded-2xl overflow-hidden">
            {restMatches.map((job, idx) => (
              <div
                key={job.id}
                onClick={onOpenJobs}
                className={`flex items-center gap-4 px-5 py-3.5 cursor-pointer hover:bg-surface-container-high transition-colors duration-150 ${idx !== restMatches.length - 1 ? 'border-b border-outline-variant/10' : ''}`}
              >
                <div className="w-9 h-9 rounded-lg bg-surface-container-lowest border border-outline-variant/10 flex items-center justify-center shrink-0">
                  <ClipboardList className="w-4 h-4 text-on-surface-variant" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px] font-semibold text-on-surface truncate">{job.title}</div>
                  <div className="text-xs text-on-surface-variant mt-0.5">{job.company}</div>
                </div>
                <span className="text-sm font-semibold tabular-nums text-on-surface-variant shrink-0">{Math.round(job.match_score || 0)}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default DashboardView;
