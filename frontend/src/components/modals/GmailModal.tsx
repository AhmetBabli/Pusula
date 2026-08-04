import React, { useState, useEffect } from 'react';
import CyberModal from '../ui/CyberModal';
import { Shield, Link } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';

function GmailModal({ isOpen, onClose, onLink, isLoading }) {
  const { t } = useLanguage();
  const [form, setForm] = useState({ email: '', password: '' });

  // Sadece modal İLK AÇILDIĞINDA inputları temizle
  useEffect(() => {
    if (isOpen) {
      setForm({ email: '', password: '' });
    }
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault(); // Sayfa yenilenmesini engelle

    // Güvenlik ve yüklenme kontrolü
    if (!form.email.trim() || !form.password.trim() || isLoading) return;

    // Veriyi gönder (temizleme işlemini burada YAPMIYORUZ)
    // Başarılı olursa App.jsx zaten modalı kapatacak.
    onLink(form.email.trim(), form.password.trim());
  };

  return (
    <CyberModal isOpen={isOpen} onClose={onClose} title={t('gmail_modal_title')}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex items-start gap-3 p-4 rounded-md bg-primary-container/5 border border-primary-container/20 text-sm text-on-surface-variant" role="note">
          <Shield className="w-5 h-5 text-primary shrink-0 mt-0.5" aria-hidden="true" />
          <p>
            {t('gmail_modal_info')}
            <br />
            <small className="text-on-surface-variant/70">{t('gmail_modal_info_path')}</small>
          </p>
        </div>

        <fieldset className="flex flex-col gap-3 border-none m-0 p-0">
          <input
            name="email"
            type="email"
            className="bg-surface-container-lowest border border-outline-variant/10 text-sm text-on-surface placeholder:text-on-surface-variant/50 rounded-md transition-colors duration-150 focus:ring-0 focus:border-primary/60 py-2.5 px-4"
            placeholder={t('gmail_modal_email_placeholder')}
            aria-label={t('gmail_modal_email_placeholder')}
            value={form.email}
            onChange={handleChange}
            disabled={isLoading}
            required
            autoComplete="off"
          />

          <input
            name="password"
            type="password"
            className="bg-surface-container-lowest border border-outline-variant/10 text-sm text-on-surface placeholder:text-on-surface-variant/50 rounded-md transition-colors duration-150 focus:ring-0 focus:border-primary/60 py-2.5 px-4"
            placeholder={t('gmail_modal_password_placeholder')}
            aria-label={t('gmail_modal_password_placeholder')}
            value={form.password}
            onChange={handleChange}
            disabled={isLoading}
            required
            minLength={16}
            autoComplete="new-password"
          />
        </fieldset>

        <button
          type="submit"
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label text-sm rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
          disabled={isLoading || !form.email.trim() || !form.password.trim()}
        >
          <Link className="w-4 h-4" aria-hidden="true" />
          {isLoading ? t('gmail_modal_connecting') : t('gmail_modal_connect')}
        </button>
      </form>
    </CyberModal>
  );
}

export default GmailModal;
