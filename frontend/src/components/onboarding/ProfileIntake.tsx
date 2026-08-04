import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { GraduationCap, Code, Target, Languages, X, ArrowRight, AlertCircle } from 'lucide-react';
import { getProfile, updateProfile } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';
import { UNIVERSITY_SUGGESTIONS, SKILL_SUGGESTIONS, SECTOR_SUGGESTIONS, LANGUAGE_SUGGESTIONS } from '../../data/suggestions';

interface IntakeData {
  university: string;
  department: string;
  graduation_year: number | null;
  skills: string[];
  target_sectors: string[];
  languages: string[];
  linkedin_url: string;
  github_url: string;
  summary: string;
}

const EMPTY: IntakeData = {
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

interface ProfileIntakeProps {
  onComplete: () => void;
}

const INPUT_CLASS = "w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 font-body text-base text-on-surface focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all";

function SuggestionDropdown({ items, onPick }: { items: string[]; onPick: (v: string) => void }) {
  if (items.length === 0) return null;
  return (
    <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-surface-container-highest border border-outline-variant/15 rounded-lg shadow-xl max-h-48 overflow-y-auto">
      {items.map((item) => (
        <button
          key={item}
          type="button"
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => onPick(item)}
          className="w-full text-left px-4 py-2.5 text-sm font-body text-on-surface hover:bg-primary-container/10 transition-colors"
        >
          {item}
        </button>
      ))}
    </div>
  );
}

function AutocompleteInput({ label, icon: Icon, value, onChange, suggestions, required }: {
  label: string;
  icon: React.ElementType;
  value: string;
  onChange: (next: string) => void;
  suggestions: string[];
  required?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const query = value.trim().toLowerCase();
  const filtered = query
    ? suggestions.filter((s) => s.toLowerCase().includes(query)).slice(0, 8)
    : suggestions.slice(0, 8);

  return (
    <div className="space-y-2 relative">
      <label className="font-label text-sm text-on-surface-variant flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5" /> {label} {required && '*'}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className={INPUT_CLASS}
      />
      {open && <SuggestionDropdown items={filtered} onPick={(v) => { onChange(v); setOpen(false); }} />}
    </div>
  );
}

function TagInput({ label, icon: Icon, values, onChange, placeholder, suggestions = [] }: {
  label: string;
  icon: React.ElementType;
  values: string[];
  onChange: (next: string[]) => void;
  placeholder: string;
  suggestions?: string[];
}) {
  const [inputValue, setInputValue] = useState('');
  const [open, setOpen] = useState(false);

  const remove = (v: string) => onChange(values.filter((x) => x !== v));
  const add = (v: string) => {
    const trimmed = v.trim();
    if (trimmed && !values.includes(trimmed)) onChange([...values, trimmed]);
    setInputValue('');
    setOpen(false);
  };

  const query = inputValue.trim().toLowerCase();
  const filtered = suggestions
    .filter((s) => !values.includes(s) && (query ? s.toLowerCase().includes(query) : true))
    .slice(0, 8);

  return (
    <div className="space-y-2 relative">
      <label className="font-label text-sm text-on-surface-variant flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5" /> {label}
      </label>
      <div className="bg-surface-container-lowest border border-outline-variant/15 rounded-lg p-3 min-h-[56px]">
        <div className="flex flex-wrap gap-2">
          {values.map((v) => (
            <div key={v} className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface px-3 py-1.5 rounded-md border border-outline-variant/10 font-label text-sm group cursor-default">
              {v}
              <button
                type="button"
                onClick={() => remove(v)}
                className="text-on-surface-variant hover:text-error transition-colors ml-1 opacity-0 group-hover:opacity-100 focus:opacity-100 outline-none"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          <input
            type="text"
            value={inputValue}
            placeholder={placeholder}
            className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-sm text-on-surface min-w-[160px] placeholder-on-surface-variant/40 p-1"
            onChange={(e) => { setInputValue(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            onBlur={() => setOpen(false)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && inputValue.trim()) {
                e.preventDefault();
                add(inputValue);
              }
            }}
          />
        </div>
      </div>
      {open && <SuggestionDropdown items={filtered} onPick={add} />}
    </div>
  );
}

export const ProfileIntake: React.FC<ProfileIntakeProps> = ({ onComplete }) => {
  const { t } = useLanguage();
  const [data, setData] = useState<IntakeData>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProfile()
      .then((p: any) => {
        setData({
          university: p.university || '',
          department: p.department || '',
          graduation_year: p.graduation_year ?? null,
          skills: p.skills || [],
          target_sectors: p.target_sectors || [],
          languages: p.languages || [],
          linkedin_url: p.linkedin_url || '',
          github_url: p.github_url || '',
          summary: p.summary || '',
        });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const isValid = data.university.trim() && data.department.trim() && data.skills.length > 0 && data.target_sectors.length > 0;

  const handleSubmit = async () => {
    if (!isValid || saving) return;
    setSaving(true);
    setError(null);
    try {
      await updateProfile({ ...data, onboarding_completed: true });
      onComplete();
    } catch (err) {
      setError((err as Error).message || t('intake_save_error'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen bg-surface" />;
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-surface text-on-surface px-6 py-12">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-headline font-semibold text-on-surface mb-2">{t('intake_title')}</h2>
          <p className="text-on-surface-variant font-body">
            {t('intake_subtitle')}
          </p>
        </div>

        <div className="bg-surface-container border border-outline-variant/15 rounded-xl p-6 md:p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <AutocompleteInput
              label={t('intake_university')}
              icon={GraduationCap}
              value={data.university}
              onChange={(v) => setData({ ...data, university: v })}
              suggestions={UNIVERSITY_SUGGESTIONS}
              required
            />
            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">{t('intake_department')} *</label>
              <input
                type="text"
                value={data.department}
                onChange={(e) => setData({ ...data, department: e.target.value })}
                className={INPUT_CLASS}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <label className="font-label text-sm text-on-surface-variant block">{t('intake_graduation_year')}</label>
              <input
                type="number"
                value={data.graduation_year ?? ''}
                onChange={(e) => setData({ ...data, graduation_year: e.target.value ? parseInt(e.target.value, 10) : null })}
                className={`w-full md:w-1/2 ${INPUT_CLASS} [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none`}
              />
            </div>
          </div>

          <TagInput label={`${t('intake_skills')} *`} icon={Code} values={data.skills} onChange={(v) => setData({ ...data, skills: v })} placeholder={t('intake_skill_placeholder')} suggestions={SKILL_SUGGESTIONS} />
          <TagInput label={`${t('intake_sectors')} *`} icon={Target} values={data.target_sectors} onChange={(v) => setData({ ...data, target_sectors: v })} placeholder={t('intake_sector_placeholder')} suggestions={SECTOR_SUGGESTIONS} />
          <TagInput label={t('intake_languages')} icon={Languages} values={data.languages} onChange={(v) => setData({ ...data, languages: v })} placeholder={t('intake_language_placeholder')} suggestions={LANGUAGE_SUGGESTIONS} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">LinkedIn</label>
              <input
                type="url"
                value={data.linkedin_url}
                onChange={(e) => setData({ ...data, linkedin_url: e.target.value })}
                placeholder="https://linkedin.com/in/..."
                className={INPUT_CLASS}
              />
            </div>
            <div className="space-y-2">
              <label className="font-label text-sm text-on-surface-variant block">GitHub</label>
              <input
                type="url"
                value={data.github_url}
                onChange={(e) => setData({ ...data, github_url: e.target.value })}
                placeholder="https://github.com/..."
                className={INPUT_CLASS}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="font-label text-sm text-on-surface-variant block">{t('intake_summary')}</label>
            <textarea
              value={data.summary}
              onChange={(e) => setData({ ...data, summary: e.target.value })}
              rows={3}
              className={`${INPUT_CLASS} resize-none`}
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-error/10 border border-error/20 text-error text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" /> {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!isValid || saving}
            className="w-full flex items-center justify-center gap-2 py-3.5 bg-primary-container hover:bg-blue-700 text-white text-sm font-label rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saving ? t('intake_saving') : t('intake_continue')}
            {!saving && <ArrowRight className="w-4 h-4" />}
          </button>
          {!isValid && (
            <p className="text-xs text-on-surface-variant text-center">
              {t('intake_validation_hint')}
            </p>
          )}
        </div>
      </motion.div>
    </div>
  );
};
