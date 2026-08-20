import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Briefcase, Search, MapPin, Building, Star, ExternalLink, Activity, AlertCircle, Compass } from 'lucide-react';
import CyberModal from '../ui/CyberModal';
import Dropdown from '../ui/Dropdown';
import * as api from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

const JOB_TYPE_KEYS = {
  staj: 'jobs_type_staj',
  tam_zamanlı: 'jobs_type_tam_zamanli',
  iş: 'jobs_type_is',
};

const STATUS_KEYS = {
  new: 'jobs_status_new',
  reviewed: 'jobs_status_reviewed',
  applying: 'jobs_status_applying',
  applied: 'jobs_status_applied',
};

const SOURCE_LABELS = {
  kariyer_net: 'Kariyer.net',
  youthall: 'Youthall',
  linkedin: 'LinkedIn',
  arbeitnow: 'Arbeitnow',
};

// Kazınan konum metinleri tutarsız ("İstanbul (Hibrit)", "İstanbul +1 il daha",
// "İstanbul(Asya)"...) — filtre için asıl şehir adını ayıklıyoruz.
const cityFromLocation = (location) => {
  if (!location) return '';
  return location.split(/[(+,]/)[0].trim();
};

// Tüm ilanlar tek seferde DOM'a basılmasın diye sayfa sayfa gösteriyoruz.
const JOBS_PAGE_SIZE = 20;

function JobsView({ jobs, isLoading, onJobAction }) {
  const { t } = useLanguage();
  const jobTypeLabel = (jobType) => (jobType && JOB_TYPE_KEYS[jobType] ? t(JOB_TYPE_KEYS[jobType]) : jobType);
  const statusLabel = (status) => (status && STATUS_KEYS[status] ? t(STATUS_KEYS[status]) : status);
  const sourceLabel = (source) => (source && SOURCE_LABELS[source]) || source;

  const [searchQuery, setSearchQuery] = useState('');
  const [filterSource, setFilterSource] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterCity, setFilterCity] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [sortBy, setSortBy] = useState('match_score');
  const [preparing, setPreparing] = useState(false);
  const [prepareError, setPrepareError] = useState(null);
  const [visibleCount, setVisibleCount] = useState(JOBS_PAGE_SIZE);

  // Arama/filtre/sıralama değişince baştan başla — yoksa kullanıcı 80. ilanı
  // görürken filtre değiştirir, liste küçülür ama kaydırma konumu tuhaf kalır.
  useEffect(() => {
    setVisibleCount(JOBS_PAGE_SIZE);
  }, [searchQuery, filterSource, filterStatus, filterType, filterCity, sortBy]);

  const handleCardClick = async (job) => {
    setDetailLoading(true);
    setPrepareError(null);
    try {
      const detail = await api.getJobDetail(job.id);
      setSelectedJob(detail);
    } catch (err) {
      setSelectedJob(job);
    } finally {
      setDetailLoading(false);
    }
  };

  const handlePrepare = async () => {
    if (preparing || !selectedJob) return;
    setPreparing(true);
    setPrepareError(null);
    try {
      await onJobAction('prepare', selectedJob.id);
      setSelectedJob(null);
    } catch (err) {
      setPrepareError(err.message || t('jobs_prepare_error_fallback'));
    } finally {
      setPreparing(false);
    }
  };

  const filteredJobs = jobs
    .filter(job => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return (
          job.title?.toLowerCase().includes(q) ||
          job.company?.toLowerCase().includes(q) ||
          job.location?.toLowerCase().includes(q)
        );
      }
      return true;
    })
    .filter(job => !filterSource || job.source === filterSource)
    .filter(job => !filterStatus || job.status === filterStatus)
    .filter(job => !filterType || job.job_type === filterType)
    .filter(job => !filterCity || cityFromLocation(job.location) === filterCity)
    .sort((a, b) => {
      if (sortBy === 'match_score') return (b.match_score || 0) - (a.match_score || 0);
      if (sortBy === 'date') return new Date(b.deadline || 0) - new Date(a.deadline || 0);
      if (sortBy === 'company') return (a.company || '').localeCompare(b.company || '');
      return 0;
    });

  const sources = [...new Set(jobs.map(j => j.source).filter(Boolean))];
  const statuses = [...new Set(jobs.map(j => j.status).filter(Boolean))];
  const types = [...new Set(jobs.map(j => j.job_type).filter(Boolean))];
  const cities = [...new Set(jobs.map(j => cityFromLocation(j.location)).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'tr'));

  const sourceOptions = [
    { value: '', label: t('jobs_all_sources') },
    ...sources.map(s => ({ value: s, label: sourceLabel(s) })),
  ];
  const statusOptions = [
    { value: '', label: t('jobs_all_statuses') },
    ...statuses.map(s => ({ value: s, label: statusLabel(s) })),
  ];
  const typeOptions = [
    { value: '', label: t('jobs_all_types') },
    ...types.map(ty => ({ value: ty, label: jobTypeLabel(ty) })),
  ];
  const cityOptions = [
    { value: '', label: t('jobs_all_cities') },
    ...cities.map(c => ({ value: c, label: c })),
  ];
  const sortOptions = [
    { value: 'match_score', label: t('jobs_sort_match') },
    { value: 'date', label: t('jobs_sort_date') },
    { value: 'company', label: t('jobs_sort_company') },
  ];

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
              <Briefcase className="w-4 h-4 text-primary" />
            </div>
            <h2 className="text-3xl font-headline font-bold text-on-surface tracking-tight">{t('jobs_title')}</h2>
          </div>
          <p className="text-sm text-on-surface-variant flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {jobs.length} {t('jobs_active_suffix')}
          </p>
        </div>
      </motion.div>

      {/* Filter Bar */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05, duration: 0.3 }}
        className="flex flex-wrap gap-3 items-center bg-surface-container border border-outline-variant/10 p-2 rounded-lg"
      >
        <div className="flex-1 min-w-[200px] flex items-center gap-2 bg-surface-container-lowest px-4 py-2 rounded-md border border-outline-variant/10 focus-within:border-primary/50 transition-colors duration-150">
          <Search className="w-4 h-4 text-on-surface-variant" />
          <input
            type="text"
            placeholder={t('jobs_search_placeholder')}
            aria-label={t('jobs_search_placeholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent border-none w-full text-sm font-body text-on-surface placeholder:text-on-surface-variant/50 focus:ring-0 p-0"
          />
        </div>

        <Dropdown value={filterType} onChange={setFilterType} options={typeOptions} className="min-w-[150px]" ariaLabel={t('jobs_all_types')} />
        <Dropdown value={filterCity} onChange={setFilterCity} options={cityOptions} className="min-w-[150px]" ariaLabel={t('jobs_all_cities')} />
        <Dropdown value={filterSource} onChange={setFilterSource} options={sourceOptions} className="min-w-[160px]" ariaLabel={t('jobs_all_sources')} />
        <Dropdown value={filterStatus} onChange={setFilterStatus} options={statusOptions} className="min-w-[160px]" ariaLabel={t('jobs_all_statuses')} />
        <Dropdown value={sortBy} onChange={setSortBy} options={sortOptions} className="min-w-[160px]" ariaLabel={t('jobs_sort_match')} />
      </motion.div>

      {/* List section */}
      <div className="w-full">
        {isLoading && jobs.length === 0 ? (
          <div className="space-y-3">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-24 bg-surface-container/50 border border-outline-variant/10 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : filteredJobs.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col items-center justify-center p-16 bg-surface-container border border-outline-variant/10 rounded-lg text-center"
          >
            <div className="w-20 h-20 rounded-full bg-outline-variant/5 flex items-center justify-center mb-6">
              <Briefcase className="w-10 h-10 text-on-surface-variant/50" />
            </div>
            <p className="text-lg font-headline font-medium text-on-surface mb-2">{t('jobs_empty_title')}</p>
            <span className="text-sm font-body text-on-surface-variant">{t('jobs_empty_desc')}</span>
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-3"
          >
            <AnimatePresence>
              {filteredJobs.slice(0, visibleCount).map(job => {
                const score = Math.round(job.match_score || 0);
                const scoreColor = score > 70 ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20' : score > 40 ? 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20' : 'text-red-500 bg-red-500/10 border-red-500/20';

                return (
                  <motion.div
                    key={job.id}
                    variants={itemVariants}
                    layout
                    onClick={() => handleCardClick(job)}
                    className="group bg-surface-container hover:bg-surface-container-high border border-outline-variant/10 hover:border-outline-variant/20 p-5 rounded-lg transition-all duration-150 flex flex-col md:flex-row gap-4 md:items-center justify-between cursor-pointer"
                  >
                    <div className="flex-1 flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-headline font-medium text-on-surface group-hover:text-primary transition-colors duration-150">{job.title}</h3>
                        {job.is_favorite && <Star className="w-4 h-4 text-yellow-500" fill="currentColor" />}
                        {job.status === 'new' && <span className="px-2 py-0.5 rounded text-[10px] font-label font-bold bg-primary/15 text-primary">{t('jobs_badge_new')}</span>}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm font-body text-on-surface-variant">
                        <span className="flex items-center gap-1.5"><Building className="w-4 h-4" /> {job.company}</span>
                        {job.location && (
                          <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" /> {job.location}</span>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-2 mt-1">
                        {job.job_type && <span className="px-2.5 py-1 rounded-md bg-outline-variant/5 text-xs font-label text-on-surface/80">{jobTypeLabel(job.job_type)}</span>}
                        {job.source && <span className="px-2.5 py-1 rounded-md bg-primary-container/10 border border-primary-container/20 text-xs font-label text-primary">{sourceLabel(job.source)}</span>}
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className={`flex items-center justify-center px-4 py-2 rounded-md border font-bold text-lg tabular-nums ${scoreColor}`}>
                        {score}%
                      </div>
                      <button className="px-4 py-2 rounded-md bg-outline-variant/5 hover:bg-outline-variant/10 active:scale-[0.97] text-on-surface text-sm font-label transition-all duration-150">
                        {t('jobs_detail_button')}
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {visibleCount < filteredJobs.length && (
              <button
                onClick={() => setVisibleCount(c => c + JOBS_PAGE_SIZE)}
                className="w-full py-3 rounded-lg border border-outline-variant/15 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high text-sm font-label transition-all duration-150"
              >
                {t('jobs_load_more')} ({filteredJobs.length - visibleCount})
              </button>
            )}
          </motion.div>
        )}
      </div>

      {/* Job Detail Modal */}
      <CyberModal
        isOpen={!!selectedJob}
        onClose={() => setSelectedJob(null)}
        title={selectedJob?.title || t('jobs_detail_title_fallback')}
      >
        {selectedJob && (
          <div className="flex flex-col gap-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-headline font-semibold text-on-surface">{selectedJob.company}</h3>
                <p className="text-sm font-body text-on-surface-variant">{selectedJob.location}</p>
              </div>
              <div className={`flex items-center justify-center w-16 h-16 rounded-full border-4 font-bold text-xl tabular-nums ${
                  (selectedJob.match_score || 0) > 70 ? 'border-emerald-500/30 text-emerald-500 bg-emerald-500/10' :
                  (selectedJob.match_score || 0) > 40 ? 'border-yellow-500/30 text-yellow-500 bg-yellow-500/10' :
                  'border-red-500/30 text-red-500 bg-red-500/10'
                }`}>
                {Math.round(selectedJob.match_score || 0)}%
              </div>
            </div>

            {selectedJob.description && (
              <div className="space-y-2">
                <h4 className="text-sm font-label text-on-surface-variant">{t('jobs_description')}</h4>
                <p className="text-sm font-body text-on-surface leading-relaxed p-4 rounded-md bg-surface-container-lowest border border-outline-variant/10 whitespace-pre-wrap">
                  {selectedJob.description}
                </p>
              </div>
            )}

            {selectedJob.requirements && (
              <div className="space-y-2">
                <h4 className="text-sm font-label text-on-surface-variant">{t('jobs_requirements')}</h4>
                <p className="text-sm font-body text-on-surface leading-relaxed p-4 rounded-md bg-surface-container-lowest border border-outline-variant/10 whitespace-pre-wrap">
                  {selectedJob.requirements}
                </p>
              </div>
            )}

            {selectedJob.match_explanation && (
              <div className="space-y-2">
                <h4 className="text-sm font-label font-semibold text-primary flex items-center gap-2">
                  <Activity className="w-4 h-4" /> {t('jobs_ai_evaluation')}
                </h4>
                <p className="text-sm font-body text-on-surface leading-relaxed p-4 rounded-md bg-primary-container/5 border border-primary-container/20 whitespace-pre-wrap">
                  {selectedJob.match_explanation}
                </p>
              </div>
            )}

            {prepareError && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
                {prepareError}
              </div>
            )}

            <div className="flex gap-3 pt-4 border-t border-outline-variant/10 mt-2">
              <button
                className="flex-1 py-3 px-4 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label rounded-md transition-all duration-150 text-center disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                onClick={handlePrepare}
                disabled={preparing}
              >
                {preparing && <Compass className="w-4 h-4 animate-spin" />}
                {preparing ? t('jobs_preparing') : t('jobs_prepare_application')}
              </button>
              {selectedJob.source_url && (
                <a
                  href={selectedJob.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-3 px-4 bg-surface-container hover:bg-surface-container-high active:scale-[0.98] border border-outline-variant/15 text-on-surface font-label rounded-md transition-all duration-150 flex items-center justify-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" /> {t('jobs_go_to_listing')}
                </a>
              )}
            </div>
          </div>
        )}
      </CyberModal>
    </div>
  );
}

export default JobsView;
