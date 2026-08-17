import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Check, Save, X, LogOut, KeyRound, ExternalLink, CheckCircle2, Pencil, Eye, EyeOff, Compass } from 'lucide-react';
import { updateProfile } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';
import { useTour } from '../../tour/TourContext';

export interface UserProfile {
  id?: number;
  full_name: string;
  email?: string;
  phone?: string;
  university?: string;
  department?: string;
  graduation_year?: number | null;
  target_sectors?: string[];
  skills?: string[];
  languages?: string[];
  linkedin_url?: string;
  github_url?: string;
  summary?: string;
  has_gemini_api_key?: boolean;
}

const EMPTY_PROFILE: UserProfile = {
  full_name: '',
  university: '',
  department: '',
  graduation_year: null,
  skills: [],
  target_sectors: [],
  languages: [],
  linkedin_url: '',
  github_url: '',
  summary: '',
};

interface ProfileViewProps {
  userProfile: UserProfile | null;
  onSave: (profile: UserProfile) => void;
  onLogout: () => void;
}

function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  return parts.slice(0, 2).map(p => p[0]?.toUpperCase()).join('');
}

export const ProfileView: React.FC<ProfileViewProps> = ({ userProfile, onSave, onLogout }) => {
  const { t } = useLanguage();
  const { start: startTour } = useTour();
  const [formData, setFormData] = useState<UserProfile>(userProfile || EMPTY_PROFILE);
  const [isSaved, setIsSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [geminiKeyInput, setGeminiKeyInput] = useState('');
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [removingKey, setRemovingKey] = useState(false);
  const [editingIdentity, setEditingIdentity] = useState(false);

  const toggleSkill = (skill: string) => {
    setFormData(prev => ({
      ...prev,
      skills: (prev.skills || []).includes(skill)
        ? (prev.skills || []).filter(s => s !== skill)
        : [...(prev.skills || []), skill],
    }));
  };

  const toggleSector = (sector: string) => {
    setFormData(prev => ({
      ...prev,
      target_sectors: (prev.target_sectors || []).includes(sector)
        ? (prev.target_sectors || []).filter(s => s !== sector)
        : [...(prev.target_sectors || []), sector],
    }));
  };

  const toggleLanguage = (lang: string) => {
    setFormData(prev => ({
      ...prev,
      languages: (prev.languages || []).includes(lang)
        ? (prev.languages || []).filter(l => l !== lang)
        : [...(prev.languages || []), lang],
    }));
  };

  const handleDiscard = () => {
    setFormData(userProfile || EMPTY_PROFILE);
    setEditingIdentity(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        full_name: formData.full_name,
        phone: formData.phone,
        university: formData.university,
        department: formData.department,
        graduation_year: formData.graduation_year || undefined,
        target_sectors: formData.target_sectors,
        skills: formData.skills,
        languages: formData.languages,
        linkedin_url: formData.linkedin_url,
        github_url: formData.github_url,
        summary: formData.summary,
      };
      // Sadece kullanıcı gerçekten yeni bir key yazdıysa gönder — boşsa
      // mevcut kayıtlı key'i yanlışlıkla silmeyelim.
      if (geminiKeyInput.trim()) {
        payload.gemini_api_key = geminiKeyInput.trim();
      }
      await updateProfile(payload);
      onSave({ ...formData, has_gemini_api_key: formData.has_gemini_api_key || !!geminiKeyInput.trim() });
      setGeminiKeyInput('');
      setShowGeminiKey(false);
      setEditingIdentity(false);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      setError((err as Error).message || t('profile_save_error'));
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveGeminiKey = async () => {
    setRemovingKey(true);
    setError(null);
    try {
      await updateProfile({ gemini_api_key: '' });
      setGeminiKeyInput('');
      onSave({ ...formData, has_gemini_api_key: false });
      setFormData(prev => ({ ...prev, has_gemini_api_key: false }));
    } catch (err) {
      setError((err as Error).message || t('profile_save_error'));
    } finally {
      setRemovingKey(false);
    }
  };

  const completeness = React.useMemo(() => {
    const checks = [
      !!formData.full_name,
      !!formData.university,
      !!formData.department,
      !!formData.graduation_year,
      (formData.skills || []).length > 0,
      (formData.target_sectors || []).length > 0,
      !!formData.linkedin_url || !!formData.github_url,
      !!formData.summary,
    ];
    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
  }, [formData]);

  const summaryTags = ((formData.target_sectors && formData.target_sectors.length > 0)
    ? formData.target_sectors
    : (formData.skills || [])
  ).slice(0, 2);

  const inputClass = "w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all";
  const labelClass = "font-label text-sm text-on-surface-variant block mb-2";

  return (
    <div className="max-w-[1200px] mx-auto w-full pb-12">
      <motion.header initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-8">
        <h2 className="font-headline text-3xl md:text-4xl text-on-surface mb-2 font-semibold">{t('profile_title')}</h2>
        <p className="font-body text-base text-on-surface-variant">{t('profile_subtitle')}</p>
      </motion.header>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-xl bg-error/10 border border-error/20 text-error text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-6 items-start">
        {/* Sol sütun */}
        <div className="space-y-6">
          {/* Kişisel Bilgiler */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.05 }}
            className="bg-surface-container border border-outline-variant/10 rounded-xl p-6 md:p-7">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-headline text-lg text-on-surface font-semibold">{t('profile_identity_title')}</h3>
              {!editingIdentity && (
                <button
                  type="button"
                  onClick={() => setEditingIdentity(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-primary hover:bg-primary/10 transition-colors font-label text-sm"
                >
                  <Pencil className="w-3.5 h-3.5" /> {t('profile_edit')}
                </button>
              )}
            </div>

            {!editingIdentity ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
                <div>
                  <div className="text-xs font-label text-on-surface-variant mb-1">{t('profile_full_name')}</div>
                  <div className="text-base font-body text-on-surface">{formData.full_name || '—'}</div>
                </div>
                <div>
                  <div className="text-xs font-label text-on-surface-variant mb-1 flex items-center gap-1.5"><Mail className="w-3 h-3" /> {t('profile_email')}</div>
                  <div className="text-base font-body text-on-surface">{formData.email || '—'}</div>
                </div>
                <div>
                  <div className="text-xs font-label text-on-surface-variant mb-1">{t('profile_university')}</div>
                  <div className="text-base font-body text-on-surface">{formData.university || '—'}</div>
                </div>
                <div>
                  <div className="text-xs font-label text-on-surface-variant mb-1">{t('profile_department')}</div>
                  <div className="text-base font-body text-on-surface">{formData.department || '—'}</div>
                </div>
                <div>
                  <div className="text-xs font-label text-on-surface-variant mb-1">{t('profile_graduation_year')}</div>
                  <div className="text-base font-body text-on-surface">{formData.graduation_year || '—'}</div>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className={labelClass}>{t('profile_full_name')}</label>
                    <input type="text" value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={`${labelClass} flex items-center gap-1.5`}><Mail className="w-3.5 h-3.5" /> {t('profile_email')}</label>
                    <input type="email" value={formData.email || ''} disabled className={`${inputClass} bg-surface-container-lowest/50 border-outline-variant/10 text-on-surface-variant cursor-not-allowed`} />
                  </div>
                  <div>
                    <label className={labelClass}>{t('profile_university')}</label>
                    <input type="text" value={formData.university || ''} onChange={e => setFormData({ ...formData, university: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>{t('profile_department')}</label>
                    <input type="text" value={formData.department || ''} onChange={e => setFormData({ ...formData, department: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>{t('profile_graduation_year')}</label>
                    <input type="number" value={formData.graduation_year ?? ''} onChange={e => setFormData({ ...formData, graduation_year: e.target.value ? parseInt(e.target.value, 10) : null })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>LinkedIn</label>
                    <input type="url" value={formData.linkedin_url || ''} onChange={e => setFormData({ ...formData, linkedin_url: e.target.value })} placeholder="https://linkedin.com/in/..." className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>GitHub</label>
                    <input type="url" value={formData.github_url || ''} onChange={e => setFormData({ ...formData, github_url: e.target.value })} placeholder="https://github.com/..." className={inputClass} />
                  </div>
                </div>
                <div>
                  <label className={labelClass}>{t('profile_summary')}</label>
                  <textarea value={formData.summary || ''} onChange={e => setFormData({ ...formData, summary: e.target.value })} rows={3} className={`${inputClass} resize-none`} />
                </div>

                <div className="flex items-center justify-end gap-3 pt-2 border-t border-outline-variant/10">
                  <button type="button" onClick={handleDiscard} className="px-5 py-2.5 rounded-lg border border-outline-variant/15 text-on-surface hover:bg-outline-variant/10 transition-colors font-label text-sm">
                    {t('profile_cancel')}
                  </button>
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={saving}
                    className="px-5 py-2.5 rounded-lg bg-primary-container text-white hover:bg-blue-700 transition-colors font-label text-sm flex items-center gap-2 disabled:opacity-50"
                  >
                    {isSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                    {saving ? t('profile_saving') : isSaved ? t('profile_saved') : t('profile_save')}
                  </button>
                </div>
              </div>
            )}
          </motion.section>

          {/* Beceriler & Tercihler */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
            className="bg-surface-container border border-outline-variant/10 rounded-xl p-6 md:p-7">
            <h3 className="font-headline text-lg text-on-surface font-semibold mb-1">{t('profile_additional_title')}</h3>
            <p className="font-body text-sm text-on-surface-variant mb-6">{t('profile_additional_desc')}</p>

            <div className="space-y-5">
              <div>
                <label className={labelClass}>{t('profile_skills_title')}</label>
                <div className="bg-surface-container-lowest border border-outline-variant/15 rounded-lg p-3 min-h-[52px]">
                  <div className="flex flex-wrap gap-2">
                    {(formData.skills || []).map(skill => (
                      <div key={skill} className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface px-3 py-1.5 rounded-md border border-outline-variant/10 font-label text-sm group cursor-default">
                        {skill}
                        <button type="button" onClick={() => toggleSkill(skill)} className="text-on-surface-variant hover:text-error transition-colors ml-1 opacity-0 group-hover:opacity-100 focus:opacity-100 outline-none">
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                    <input
                      type="text"
                      placeholder={t('profile_skill_placeholder')}
                      className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-sm text-on-surface min-w-[160px] placeholder-on-surface-variant/40 p-1"
                      onKeyDown={(e) => { if (e.key === 'Enter' && e.currentTarget.value.trim()) { toggleSkill(e.currentTarget.value.trim()); e.currentTarget.value = ''; } }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className={labelClass}>{t('profile_sectors_title')}</label>
                <div className="bg-surface-container-lowest border border-outline-variant/15 rounded-lg p-3 min-h-[52px]">
                  <div className="flex flex-wrap gap-2">
                    {(formData.target_sectors || []).map(sector => (
                      <div key={sector} className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface px-3 py-1.5 rounded-md border border-outline-variant/10 font-label text-sm group cursor-default">
                        {sector}
                        <button type="button" onClick={() => toggleSector(sector)} className="text-on-surface-variant hover:text-error transition-colors ml-1 opacity-0 group-hover:opacity-100 focus:opacity-100 outline-none">
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                    <input
                      type="text"
                      placeholder={t('profile_sector_placeholder')}
                      className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-sm text-on-surface min-w-[160px] placeholder-on-surface-variant/40 p-1"
                      onKeyDown={(e) => { if (e.key === 'Enter' && e.currentTarget.value.trim()) { toggleSector(e.currentTarget.value.trim()); e.currentTarget.value = ''; } }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className={labelClass}>{t('profile_languages_title')}</label>
                <div className="bg-surface-container-lowest border border-outline-variant/15 rounded-lg p-3 min-h-[52px]">
                  <div className="flex flex-wrap gap-2">
                    {(formData.languages || []).map(lang => (
                      <div key={lang} className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface px-3 py-1.5 rounded-md border border-outline-variant/10 font-label text-sm group cursor-default">
                        {lang}
                        <button type="button" onClick={() => toggleLanguage(lang)} className="text-on-surface-variant hover:text-error transition-colors ml-1 opacity-0 group-hover:opacity-100 focus:opacity-100 outline-none">
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                    <input
                      type="text"
                      placeholder={t('profile_language_placeholder')}
                      className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-sm text-on-surface min-w-[160px] placeholder-on-surface-variant/40 p-1"
                      onKeyDown={(e) => { if (e.key === 'Enter' && e.currentTarget.value.trim()) { toggleLanguage(e.currentTarget.value.trim()); e.currentTarget.value = ''; } }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-5 mt-5 border-t border-outline-variant/10">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="px-5 py-2.5 rounded-lg bg-primary-container text-white hover:bg-blue-700 transition-colors font-label text-sm flex items-center gap-2 disabled:opacity-50"
              >
                {isSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                {saving ? t('profile_saving') : isSaved ? t('profile_saved') : t('profile_save')}
              </button>
            </div>
          </motion.section>

          {/* Entegrasyonlar */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }}
            className="bg-surface-container border border-outline-variant/10 rounded-xl p-6 md:p-7">
            <h3 className="font-headline text-lg text-on-surface font-semibold mb-5">{t('profile_integrations_title')}</h3>

            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <KeyRound className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-label text-sm font-semibold text-on-surface">{t('profile_gemini_key_title')}</span>
                  {formData.has_gemini_api_key && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-label font-medium text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3 h-3" /> {t('profile_gemini_key_badge_active')}
                    </span>
                  )}
                </div>
                <p className="text-xs text-on-surface-variant mt-0.5">{t('profile_integrations_desc')}</p>
              </div>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-56">
                  <input
                    type={showGeminiKey ? 'text' : 'password'}
                    value={geminiKeyInput}
                    onChange={e => setGeminiKeyInput(e.target.value)}
                    placeholder={formData.has_gemini_api_key ? t('profile_gemini_key_placeholder_set') : t('profile_gemini_key_placeholder_empty')}
                    autoComplete="off"
                    className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-md pl-3 pr-9 py-2.5 font-body text-sm text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowGeminiKey(v => !v)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface transition-colors"
                    aria-label={showGeminiKey ? t('profile_gemini_key_hide') : t('profile_gemini_key_show')}
                  >
                    {showGeminiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving || !geminiKeyInput.trim()}
                  className="px-4 py-2.5 rounded-md bg-primary-container text-white hover:bg-blue-700 active:scale-[0.98] transition-all font-label text-sm whitespace-nowrap disabled:opacity-50"
                >
                  {t('profile_gemini_key_renew')}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between mt-4">
              <a
                href="https://aistudio.google.com/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline underline-offset-2"
              >
                {t('profile_gemini_key_get_one')} <ExternalLink className="w-3 h-3" />
              </a>
              {formData.has_gemini_api_key && (
                <button
                  type="button"
                  onClick={handleRemoveGeminiKey}
                  disabled={removingKey}
                  className="text-xs text-error hover:underline underline-offset-2 disabled:opacity-50"
                >
                  {t('profile_gemini_key_remove')}
                </button>
              )}
            </div>
          </motion.section>
        </div>

        {/* Sağ sütun — Profil özeti */}
        <motion.aside initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.05 }}
          className="bg-surface-container border border-outline-variant/10 rounded-xl p-6 flex flex-col items-center text-center lg:sticky lg:top-6">
          <div className="w-20 h-20 rounded-full bg-primary/10 border border-primary/20 text-primary flex items-center justify-center text-2xl font-headline font-semibold mb-4">
            {getInitials(formData.full_name)}
          </div>
          <div className="text-lg font-headline font-semibold text-on-surface">{formData.full_name || '—'}</div>
          <div className="text-sm text-on-surface-variant mt-0.5">{formData.department || formData.university || ' '}</div>

          {summaryTags.length > 0 && (
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {summaryTags.map(tag => (
                <span key={tag} className="text-xs font-label px-2.5 py-1 rounded-full bg-primary/10 text-primary">{tag}</span>
              ))}
            </div>
          )}

          <div className="w-full mt-6 pt-5 border-t border-outline-variant/10">
            <div className="flex items-center justify-between text-xs font-label text-on-surface-variant mb-2">
              <span>{t('profile_completeness')}</span>
              <span className="font-semibold text-on-surface tabular-nums">%{completeness}</span>
            </div>
            <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full transition-all duration-500" style={{ width: `${completeness}%` }} />
            </div>
          </div>

          <button
            type="button"
            onClick={startTour}
            className="w-full mt-6 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-outline-variant/15 text-on-surface hover:bg-outline-variant/10 transition-colors font-label text-sm"
          >
            <Compass className="w-4 h-4" /> {t('profile_restart_tour')}
          </button>

          <button
            type="button"
            onClick={onLogout}
            className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-error/20 text-error hover:bg-error/10 transition-colors font-label text-sm"
          >
            <LogOut className="w-4 h-4" /> {t('profile_logout')}
          </button>
        </motion.aside>
      </div>
    </div>
  );
};
