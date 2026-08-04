import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, GraduationCap, Check, Save, Code, Target, Languages, Link2, X, LogOut } from 'lucide-react';
import { updateProfile } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

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

export const ProfileView: React.FC<ProfileViewProps> = ({ userProfile, onSave, onLogout }) => {
  const { t } = useLanguage();
  const [formData, setFormData] = useState<UserProfile>(userProfile || EMPTY_PROFILE);
  const [isSaved, setIsSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleDiscard = () => setFormData(userProfile || EMPTY_PROFILE);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await updateProfile({
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
      });
      onSave(formData);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      setError((err as Error).message || t('profile_save_error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-[900px] mx-auto w-full relative pb-12">
      <motion.header initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="mb-10 flex items-start justify-between gap-4">
        <div>
          <h2 className="font-headline text-3xl md:text-4xl text-on-surface mb-2 font-semibold">{t('profile_title')}</h2>
          <p className="font-body text-base text-on-surface-variant">{t('profile_subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-error/20 bg-error/10 text-error hover:bg-error/20 transition-colors font-label text-sm shrink-0"
        >
          <LogOut className="w-4 h-4" /> {t('profile_logout')}
        </button>
      </motion.header>

      <form className="space-y-8" onSubmit={e => e.preventDefault()}>
        <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}
          className="bg-surface-container border border-outline-variant/15 rounded-xl p-6 md:p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary-container/20"></div>

          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-surface-container-high border border-outline-variant/10 flex items-center justify-center text-primary">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-headline text-xl text-on-surface">{t('profile_identity_title')}</h3>
              <p className="font-body text-sm text-on-surface-variant">{t('profile_identity_desc')}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">{t('profile_full_name')}</label>
              <input
                type="text"
                value={formData.full_name}
                onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" /> {t('profile_email')}
              </label>
              <input
                type="email"
                value={formData.email || ''}
                disabled
                className="w-full bg-surface-container-lowest/50 border border-outline-variant/10 rounded-lg px-4 py-3 font-body text-base text-on-surface-variant cursor-not-allowed"
              />
            </div>

            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">{t('profile_university')}</label>
              <input
                type="text"
                value={formData.university || ''}
                onChange={e => setFormData({ ...formData, university: e.target.value })}
                className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">{t('profile_department')}</label>
              <input
                type="text"
                value={formData.department || ''}
                onChange={e => setFormData({ ...formData, department: e.target.value })}
                className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">{t('profile_graduation_year')}</label>
              <input
                type="number"
                value={formData.graduation_year ?? ''}
                onChange={e => setFormData({ ...formData, graduation_year: e.target.value ? parseInt(e.target.value, 10) : null })}
                className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
              />
            </div>
          </div>
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-surface-container border border-outline-variant/15 rounded-xl p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-surface-container-high border border-outline-variant/10 flex items-center justify-center text-primary">
              <Code className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-headline text-xl text-on-surface">{t('profile_skills_title')}</h3>
              <p className="font-body text-sm text-on-surface-variant">{t('profile_skills_desc')}</p>
            </div>
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant/15 rounded-lg p-4 min-h-[120px]">
            <div className="flex flex-wrap gap-2">
              {(formData.skills || []).map(skill => (
                <div key={skill} className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface px-3 py-1.5 rounded-md border border-outline-variant/10 font-label text-sm group cursor-default">
                  {skill}
                  <button
                    type="button"
                    onClick={() => toggleSkill(skill)}
                    className="text-on-surface-variant hover:text-error transition-colors ml-1 opacity-0 group-hover:opacity-100 focus:opacity-100 outline-none"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <input
                type="text"
                placeholder={t('profile_skill_placeholder')}
                className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-body text-sm text-on-surface min-w-[200px] placeholder-on-surface-variant/40 p-1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                    toggleSkill(e.currentTarget.value.trim());
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.15 }}
          className="bg-surface-container border border-outline-variant/10 rounded-lg p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-md bg-surface-container-high border border-outline-variant/10 flex items-center justify-center text-primary">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-headline text-xl text-on-surface font-semibold">{t('profile_sectors_title')}</h3>
              <p className="font-body text-sm text-on-surface-variant">{t('profile_sectors_desc')}</p>
            </div>
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant/10 rounded-md p-4 min-h-[120px]">
            <div className="flex flex-wrap gap-2">
              {(formData.target_sectors || []).map(sector => (
                <div key={sector} className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface px-3 py-1.5 rounded-md border border-outline-variant/10 font-label text-sm group cursor-default">
                  {sector}
                  <button
                    type="button"
                    onClick={() => toggleSector(sector)}
                    className="text-on-surface-variant hover:text-error transition-colors duration-150 ml-1 opacity-0 group-hover:opacity-100 focus:opacity-100 outline-none"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <input
                type="text"
                placeholder={t('profile_sector_placeholder')}
                className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-body text-sm text-on-surface min-w-[200px] placeholder-on-surface-variant/40 p-1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                    toggleSector(e.currentTarget.value.trim());
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.2 }}
          className="bg-surface-container border border-outline-variant/10 rounded-lg p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-md bg-surface-container-high border border-outline-variant/10 flex items-center justify-center text-primary">
              <Languages className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-headline text-xl text-on-surface font-semibold">{t('profile_languages_title')}</h3>
              <p className="font-body text-sm text-on-surface-variant">{t('profile_languages_desc')}</p>
            </div>
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant/10 rounded-md p-4 min-h-[120px]">
            <div className="flex flex-wrap gap-2">
              {(formData.languages || []).map(lang => (
                <div key={lang} className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface px-3 py-1.5 rounded-md border border-outline-variant/10 font-label text-sm group cursor-default">
                  {lang}
                  <button
                    type="button"
                    onClick={() => toggleLanguage(lang)}
                    className="text-on-surface-variant hover:text-error transition-colors duration-150 ml-1 opacity-0 group-hover:opacity-100 focus:opacity-100 outline-none"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <input
                type="text"
                placeholder={t('profile_language_placeholder')}
                className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-body text-sm text-on-surface min-w-[200px] placeholder-on-surface-variant/40 p-1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                    toggleLanguage(e.currentTarget.value.trim());
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }}
          className="bg-surface-container border border-outline-variant/15 rounded-xl p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-surface-container-high border border-outline-variant/10 flex items-center justify-center text-primary">
              <Link2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-headline text-xl text-on-surface">{t('profile_links_title')}</h3>
              <p className="font-body text-sm text-on-surface-variant">{t('profile_links_desc')}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">LinkedIn</label>
              <input
                type="url"
                value={formData.linkedin_url || ''}
                onChange={e => setFormData({ ...formData, linkedin_url: e.target.value })}
                placeholder="https://linkedin.com/in/..."
                className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
              />
            </div>
            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">GitHub</label>
              <input
                type="url"
                value={formData.github_url || ''}
                onChange={e => setFormData({ ...formData, github_url: e.target.value })}
                placeholder="https://github.com/..."
                className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="font-label text-sm text-on-surface-variant block">{t('profile_summary')}</label>
            <textarea
              value={formData.summary || ''}
              onChange={e => setFormData({ ...formData, summary: e.target.value })}
              rows={4}
              className="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all resize-none"
            />
          </div>
        </motion.section>

        {error && (
          <div className="px-4 py-3 rounded-xl bg-error/10 border border-error/20 text-error text-sm">{error}</div>
        )}

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.4 }}
          className="flex items-center justify-end gap-4 pt-6 border-t border-outline-variant/10">
          <button type="button" onClick={handleDiscard} className="px-6 py-2.5 rounded-lg border border-outline-variant/15 text-on-surface hover:bg-outline-variant/10 transition-colors font-label text-sm">
            {t('profile_discard')}
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2.5 rounded-lg bg-primary-container text-white hover:bg-blue-700 transition-colors font-label text-sm flex items-center gap-2 shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {saving ? t('profile_saving') : isSaved ? t('profile_saved') : t('profile_save')}
          </button>
        </motion.div>
      </form>
    </div>
  );
};
