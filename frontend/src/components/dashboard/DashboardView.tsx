import React from 'react';
import {
  Briefcase, ClipboardList, TrendingUp, Star, ArrowRight,
  Zap, Shield, Search, Send,
} from 'lucide-react';
import { motion } from 'framer-motion';
import StatCard from './StatCard';
import { useLanguage } from '../../i18n/LanguageContext';

function DashboardView({
  stats,
  isLoading,
  onDeepScan,
  onSyncInbox,
  onOpenGmail,
  onOpenOutreach,
  onOpenJobs,
  onOpenApplications,
}) {
  const { t } = useLanguage();

  const statItems = [
    { icon: Briefcase, label: t('dashboard_stat_total_jobs'), value: stats?.total_jobs || 0, color: 'primary', onClick: onOpenJobs },
    { icon: Star, label: t('dashboard_stat_new_jobs'), value: stats?.new_jobs || 0, color: 'warning' },
    { icon: ClipboardList, label: t('dashboard_stat_applications'), value: stats?.total_applications || 0, color: 'secondary', onClick: onOpenApplications },
    { icon: TrendingUp, label: t('dashboard_stat_pending'), value: stats?.pending_approvals || 0, color: 'danger', onClick: onOpenApplications },
  ];

  const topMatches = (stats?.top_matches || []).slice(0, 3);

  return (
    <div className="w-full max-w-[1200px] mx-auto">
      <motion.header initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="mb-10">
        <h2 className="font-headline text-3xl md:text-4xl text-on-surface mb-2 font-bold tracking-tight">{t('dashboard_title')}</h2>
        <p className="font-body text-base text-on-surface-variant">{t('dashboard_subtitle')}</p>
      </motion.header>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.05 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {statItems.map((item, idx) => (
          <StatCard key={idx} {...item} />
        ))}
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.1 }}
        className="flex flex-wrap gap-2 mb-10">
        <button
          onClick={onDeepScan} disabled={isLoading}
          className="flex items-center gap-2 px-5 py-3 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label text-sm rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface"
        >
          <Zap className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? t('dashboard_scanning') : t('dashboard_scan_jobs')}
        </button>
        <button
          onClick={onSyncInbox} disabled={isLoading}
          className="flex items-center gap-2 px-5 py-3 bg-surface-container hover:bg-surface-container-high active:scale-[0.98] border border-outline-variant/15 text-on-surface font-label text-sm rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          <Search className="w-4 h-4" /> {t('dashboard_scan_inbox')}
        </button>
        <button
          onClick={onOpenGmail}
          className="flex items-center gap-2 px-5 py-3 bg-surface-container hover:bg-surface-container-high active:scale-[0.98] border border-outline-variant/15 text-on-surface font-label text-sm rounded-md transition-all duration-150"
        >
          <Shield className="w-4 h-4" /> {t('dashboard_connect_gmail')}
        </button>
        <button
          onClick={onOpenOutreach}
          className="flex items-center gap-2 px-5 py-3 bg-surface-container hover:bg-surface-container-high active:scale-[0.98] border border-outline-variant/15 text-on-surface font-label text-sm rounded-md transition-all duration-150"
        >
          <Send className="w-4 h-4" /> {t('dashboard_cold_email')}
        </button>
      </motion.div>

      {topMatches.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.15 }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="flex items-center gap-2 text-sm font-label text-on-surface-variant tracking-wider uppercase">
              <Star className="w-4 h-4" /> {t('dashboard_top_matches')}
            </h3>
            <button onClick={onOpenJobs} className="flex items-center gap-1 text-sm font-label text-primary hover:underline underline-offset-2">
              {t('dashboard_see_all')} <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-2">
            {topMatches.map((job) => (
              <div
                key={job.id}
                onClick={onOpenJobs}
                className="bg-surface-container hover:bg-surface-container-high border border-outline-variant/10 hover:border-outline-variant/20 rounded-lg p-4 flex items-center justify-between cursor-pointer transition-all duration-150"
              >
                <div>
                  <div className="text-base font-headline font-medium text-on-surface">{job.title}</div>
                  <div className="text-sm font-body text-on-surface-variant">{job.company}</div>
                </div>
                <div className="flex items-center gap-3 w-32">
                  <div className="text-lg font-mono font-semibold tabular-nums text-primary">{Math.round(job.match_score || 0)}%</div>
                  <div className="flex-1 h-1.5 rounded-full bg-outline-variant/10 overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: `${job.match_score || 0}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default DashboardView;
