import type { EntryFieldDef } from './EntryListEditor';

// ProfileIntake ve ProfileView'da aynı iş deneyimi/sertifika form alanları
// kullanılıyor — tekrar etmemek için tek yerden tanımlanıyor.

export function getWorkExperienceFields(t: (key: string) => string): EntryFieldDef[] {
  return [
    { key: 'title', label: t('experience_field_title'), type: 'text', required: true, placeholder: t('experience_field_title_placeholder') },
    { key: 'company', label: t('experience_field_company'), type: 'text', required: true, placeholder: t('experience_field_company_placeholder') },
    { key: 'start_date', label: t('experience_field_start'), type: 'month' },
    { key: 'end_date', label: t('experience_field_end'), type: 'month' },
    { key: 'current', label: t('experience_field_current'), type: 'checkbox' },
    { key: 'description', label: t('experience_field_description'), type: 'textarea', placeholder: t('experience_field_description_placeholder') },
  ];
}

export function getCertificateFields(t: (key: string) => string): EntryFieldDef[] {
  return [
    { key: 'name', label: t('certificate_field_name'), type: 'text', required: true, placeholder: t('certificate_field_name_placeholder') },
    { key: 'issuer', label: t('certificate_field_issuer'), type: 'text', placeholder: t('certificate_field_issuer_placeholder') },
    { key: 'date', label: t('certificate_field_date'), type: 'month' },
  ];
}

export function summarizeExperience(item: Record<string, any>, t: (key: string) => string) {
  return {
    primary: [item.title, item.company].filter(Boolean).join(' — ') || t('experience_field_title'),
    secondary: [item.start_date, item.current ? t('experience_current_label') : item.end_date].filter(Boolean).join(' - '),
  };
}

export function summarizeCertificate(item: Record<string, any>) {
  return {
    primary: item.name || '',
    secondary: [item.issuer, item.date].filter(Boolean).join(' · '),
  };
}
