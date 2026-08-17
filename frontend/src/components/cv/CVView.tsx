import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Plus, Trash2, Star, CheckCircle, AlertTriangle } from 'lucide-react';
import CyberModal from '../ui/CyberModal';
import * as api from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

function ScoreRing({ score, analyzed, pendingLabel }) {
  const pct = Math.round(score || 0);
  const tone = !analyzed ? 'rgb(var(--color-on-surface-variant))' : pct >= 70 ? '#1E7F5C' : pct >= 50 ? '#B4740E' : '#B23B3B';
  return (
    <div
      className="relative w-16 h-16 rounded-full flex items-center justify-center shrink-0"
      style={{ background: analyzed ? `conic-gradient(${tone} ${pct * 3.6}deg, rgb(var(--color-surface-container-high)) 0deg)` : 'rgb(var(--color-surface-container-high))' }}
    >
      <div className="absolute inset-[3px] rounded-full bg-surface-container-lowest flex items-center justify-center">
        {analyzed ? (
          <span className="text-base font-bold tabular-nums" style={{ color: tone }}>{pct}</span>
        ) : (
          <span className="text-[10px] font-label text-on-surface-variant text-center leading-tight px-1">{pendingLabel}</span>
        )}
      </div>
    </div>
  );
}

function CVView({ cvs, isLoading, onUpload, onDelete, onSetDefault }) {
  const { t } = useLanguage();
  const [selectedCV, setSelectedCV] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadVariant, setUploadVariant] = useState('general');

  const handleCardClick = async (cv) => {
    try {
      const detail = await api.getCVDetail(cv.id);
      setSelectedCV(detail);
    } catch (err) {
      // Fallback: use list data
      setSelectedCV(cv);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    await onUpload(uploadFile, uploadFile.name, uploadVariant);
    setShowUpload(false);
    setUploadFile(null);
  };

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
              <FileText className="w-4 h-4 text-primary" />
            </div>
            <h2 className="text-3xl font-headline font-bold text-on-surface tracking-tight">{t('cv_title')}</h2>
          </div>
          <p className="text-sm text-on-surface-variant flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {cvs.length} {t('cv_ats_active_suffix')}
          </p>
        </div>

        <button
          onClick={() => setShowUpload(true)}
          className="flex items-center gap-2 px-5 py-2.5 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white text-sm font-label rounded-md transition-all duration-150"
        >
          <Plus className="w-4 h-4" /> {t('cv_new_button')}
        </button>
      </motion.div>

      {/* List section */}
      <div className="w-full">
        {isLoading && cvs.length === 0 ? (
          <div className="space-y-3">
            {[1,2,3].map(i => (
              <div key={i} className="h-24 bg-surface-container/50 border border-outline-variant/10 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : cvs.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col items-center justify-center p-16 bg-surface-container border border-outline-variant/10 rounded-lg text-center"
          >
            <div className="w-20 h-20 rounded-full bg-outline-variant/5 flex items-center justify-center mb-6">
              <FileText className="w-10 h-10 text-on-surface-variant/50" />
            </div>
            <p className="text-lg font-headline font-medium text-on-surface mb-2">{t('cv_empty_title')}</p>
            <span className="text-sm font-body text-on-surface-variant">{t('cv_empty_desc')}</span>
          </motion.div>
        ) : (
          <motion.div variants={containerVariants} initial="hidden" animate="show" className="flex flex-col gap-8">
            {(() => {
              const defaultCV = cvs.find(cv => cv.is_default) || cvs[0];
              const otherCVs = cvs.filter(cv => cv.id !== defaultCV.id);
              const analyzed = !!defaultCV.ats_feedback;

              return (
                <>
                  <motion.div
                    variants={itemVariants}
                    onClick={() => handleCardClick(defaultCV)}
                    className="group bg-surface-container border border-primary/25 hover:border-primary/40 p-6 md:p-7 rounded-xl transition-all duration-150 flex flex-col md:flex-row gap-6 md:items-center cursor-pointer"
                  >
                    <ScoreRing score={defaultCV.ats_score} analyzed={analyzed} pendingLabel={t('cv_ats_pending')} />
                    <div className="flex-1 flex flex-col gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] font-label font-bold text-primary uppercase tracking-wide flex items-center gap-1">
                          <Star className="w-3 h-3" fill="currentColor" /> {t('cv_default_badge')}
                        </span>
                      </div>
                      <h3 className="text-xl font-headline font-medium text-on-surface group-hover:text-primary transition-colors duration-150">{defaultCV.title}</h3>
                      <div className="flex flex-wrap items-center gap-3 text-sm font-body text-on-surface-variant">
                        <span>{defaultCV.variant_type}</span>
                        <span className="px-2.5 py-1 rounded-md bg-outline-variant/5 text-xs font-label text-on-surface/80">{defaultCV.file_path ? t('cv_pdf') : t('cv_text')}</span>
                        {defaultCV.is_ai_generated && <span className="px-2 py-0.5 rounded text-[10px] font-label font-bold bg-secondary/15 text-secondary">{t('cv_ai_generated_badge')}</span>}
                      </div>
                    </div>
                    <button className="px-5 py-2.5 rounded-md bg-primary-container text-white text-sm font-label hover:bg-blue-700 active:scale-[0.97] transition-all duration-150 shrink-0">
                      {t('cv_detail_button')}
                    </button>
                  </motion.div>

                  {otherCVs.length > 0 && (
                    <div className="flex flex-col gap-3">
                      <h3 className="text-sm font-label font-semibold text-on-surface-variant">{t('cv_others_title')}</h3>
                      <AnimatePresence>
                        {otherCVs.map(cv => {
                          const cvAnalyzed = !!cv.ats_feedback;
                          const cvScore = Math.round(cv.ats_score || 0);
                          const scoreColor = !cvAnalyzed
                            ? 'text-on-surface-variant bg-outline-variant/5 border-outline-variant/15'
                            : cvScore > 70 ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20' : cvScore > 50 ? 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20' : 'text-red-500 bg-red-500/10 border-red-500/20';

                          return (
                            <motion.div
                              key={cv.id}
                              variants={itemVariants}
                              layout
                              onClick={() => handleCardClick(cv)}
                              className="group bg-surface-container hover:bg-surface-container-high border border-outline-variant/10 hover:border-outline-variant/20 p-5 rounded-lg transition-all duration-150 flex flex-col md:flex-row gap-4 md:items-center justify-between cursor-pointer"
                            >
                              <div className="flex-1 flex flex-col gap-2">
                                <div className="flex items-center gap-2">
                                  <h3 className="text-lg font-headline font-medium text-on-surface group-hover:text-primary transition-colors duration-150">{cv.title}</h3>
                                  {cv.is_ai_generated && <span className="px-2 py-0.5 rounded text-[10px] font-label font-bold bg-secondary/15 text-secondary">{t('cv_ai_generated_badge')}</span>}
                                </div>
                                <div className="flex flex-wrap items-center gap-4 text-sm font-body text-on-surface-variant">
                                  <span>{cv.variant_type}</span>
                                  <span className="px-2.5 py-1 rounded-md bg-outline-variant/5 text-xs font-label text-on-surface/80">{cv.file_path ? t('cv_pdf') : t('cv_text')}</span>
                                </div>
                              </div>
                              <div className="flex items-center gap-4">
                                <div className={`flex items-center justify-center px-4 py-2 rounded-md border font-bold text-lg tabular-nums ${scoreColor}`}>
                                  {cvAnalyzed ? cvScore : '—'}
                                </div>
                                <button className="px-4 py-2 rounded-md bg-outline-variant/5 hover:bg-outline-variant/10 active:scale-[0.97] text-on-surface text-sm font-label transition-all duration-150">
                                  {t('cv_detail_button')}
                                </button>
                              </div>
                            </motion.div>
                          );
                        })}
                      </AnimatePresence>
                    </div>
                  )}
                </>
              );
            })()}
          </motion.div>
        )}
      </div>

      {/* CV Detay Modalı */}
      <CyberModal
        isOpen={!!selectedCV}
        onClose={() => setSelectedCV(null)}
        title={selectedCV?.title || t('cv_detail_title_fallback')}
      >
        {selectedCV && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col items-center justify-center p-6 rounded-md bg-surface-container-lowest border border-outline-variant/10 text-center">
              <div className="text-5xl font-semibold tabular-nums text-on-surface">
                {selectedCV.ats_feedback ? Math.round(selectedCV.ats_score || 0) : '—'}<span className="text-2xl text-on-surface-variant">/100</span>
              </div>
              <div className="text-xs font-label text-on-surface-variant mt-2">
                {selectedCV.ats_feedback ? t('cv_ats_score') : t('cv_ats_pending')}
              </div>
            </div>

            {selectedCV.ats_feedback && (
              <div className="space-y-2">
                <h4 className="text-sm font-label font-semibold text-primary">{t('cv_ai_feedback')}</h4>
                <p className="text-sm font-body text-on-surface leading-relaxed p-4 rounded-md bg-primary-container/5 border border-primary-container/20 whitespace-pre-wrap">
                  {selectedCV.ats_feedback}
                </p>
              </div>
            )}

            {selectedCV.strengths?.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-label font-semibold text-emerald-500 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" /> {t('cv_strengths')}
                </h4>
                <ul className="space-y-2">
                  {selectedCV.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-on-surface-variant">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" /> {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {selectedCV.weaknesses?.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-label font-semibold text-secondary flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> {t('cv_weaknesses')}
                </h4>
                <ul className="space-y-2">
                  {selectedCV.weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-on-surface-variant">
                      <span className="text-secondary shrink-0 mt-0.5">•</span> {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {selectedCV.extracted_text && (
              <div className="space-y-2">
                <h4 className="text-sm font-label font-semibold text-on-surface-variant">{t('cv_content')}</h4>
                <pre className="text-xs font-mono text-on-surface-variant leading-relaxed p-4 rounded-md bg-surface-container-lowest border border-outline-variant/10 whitespace-pre-wrap max-h-64 overflow-y-auto">{selectedCV.extracted_text}</pre>
              </div>
            )}

            <div className="flex gap-3 pt-4 border-t border-outline-variant/10 mt-2">
              {!selectedCV.is_default && (
                <button
                  className="flex-1 py-3 px-4 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label rounded-md transition-all duration-150 flex items-center justify-center gap-2"
                  onClick={() => { onSetDefault(selectedCV.id); setSelectedCV(null); }}
                >
                  <Star className="w-4 h-4" /> {t('cv_set_default')}
                </button>
              )}
              <button
                className="flex-1 py-3 px-4 bg-red-500/10 hover:bg-red-500/20 active:scale-[0.98] border border-red-500/30 text-red-500 font-label rounded-md transition-all duration-150 flex items-center justify-center gap-2"
                onClick={() => { onDelete(selectedCV.id); setSelectedCV(null); }}
              >
                <Trash2 className="w-4 h-4" /> {t('cv_delete')}
              </button>
            </div>
          </div>
        )}
      </CyberModal>

      {/* Yükleme Modalı */}
      <CyberModal
        isOpen={showUpload}
        onClose={() => setShowUpload(false)}
        title={t('cv_upload_title')}
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm font-body text-on-surface-variant">{t('cv_upload_desc')}</p>
          <input
            type="file"
            accept=".pdf"
            onChange={e => setUploadFile(e.target.files[0])}
            aria-label={t('cv_upload_file_label')}
            className="text-sm text-on-surface file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary-container/15 file:text-primary file:text-sm file:font-label"
          />
          <select
            value={uploadVariant}
            onChange={e => setUploadVariant(e.target.value)}
            aria-label={t('cv_variant_select_label')}
            className="bg-surface-container-lowest border border-outline-variant/10 text-sm text-on-surface font-label rounded-md focus:ring-0 focus:border-primary/50 py-2.5 px-4"
          >
            <option value="general" className="bg-surface-container">{t('cv_variant_general')}</option>
            <option value="ai" className="bg-surface-container">{t('cv_variant_ai')}</option>
            <option value="cyber" className="bg-surface-container">{t('cv_variant_cyber')}</option>
            <option value="it" className="bg-surface-container">{t('cv_variant_it')}</option>
          </select>
          <button
            className="w-full py-3 px-4 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
            onClick={handleUpload}
            disabled={!uploadFile || isLoading}
          >
            {isLoading ? t('cv_analyzing') : t('cv_upload_and_analyze')}
          </button>
        </div>
      </CyberModal>
    </div>
  );
}

export default CVView;
