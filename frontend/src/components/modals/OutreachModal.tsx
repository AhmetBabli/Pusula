import React, { useState, useEffect } from 'react';
import CyberModal from '../ui/CyberModal';
import { Send, Building } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';

function OutreachModal({ isOpen, onClose, onSend, isLoading }) {
  const { t } = useLanguage();
  const [company, setCompany] = useState('');

  // Sadece modal İLK AÇILDIĞINDA input'u temizle (Kullanıcı iptal edip çıkmışsa eski veri kalmasın)
  useEffect(() => {
    if (isOpen) {
      setCompany('');
    }
  }, [isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault(); // Sayfa yenilenmesini (Default HTML form davranışı) engelle

    // Zaten yükleniyorsa veya boşluktan ibaretse işlemi durdur
    if (!company.trim() || isLoading) return;

    // İsteği fırlat, temizleme işini burada YAPMA.
    // İşlem başarılı olursa parent component (App.jsx) zaten modalı kapatacak.
    onSend(company.trim());
  };

  return (
    <CyberModal isOpen={isOpen} onClose={onClose} title={t('outreach_modal_title')}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex items-start gap-3 p-4 rounded-md bg-primary-container/5 border border-primary-container/20 text-sm text-on-surface-variant" role="status" aria-live="polite">
          <Building className="w-5 h-5 text-primary shrink-0 mt-0.5" aria-hidden="true" />
          <p>
            {t('outreach_modal_info')}
          </p>
        </div>

        <fieldset className="flex flex-col gap-2 border-none m-0 p-0">
          <label htmlFor="target-company" className="text-sm font-label text-on-surface-variant">{t('outreach_modal_company_label')}</label>
          <input
            id="target-company"
            type="text"
            className="bg-surface-container-lowest border border-outline-variant/10 text-sm text-on-surface placeholder:text-on-surface-variant/50 rounded-md transition-colors duration-150 focus:ring-0 focus:border-primary/60 py-2.5 px-4"
            placeholder={t('outreach_modal_company_placeholder')}
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            disabled={isLoading}
            required
            autoFocus
          />
        </fieldset>

        <button
          type="submit"
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label text-sm rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
          disabled={isLoading || !company.trim()}
        >
          <Send className="w-4 h-4" aria-hidden="true" />
          {isLoading ? t('outreach_modal_sending') : t('outreach_modal_send')}
        </button>
      </form>
    </CyberModal>
  );
}

export default OutreachModal;
