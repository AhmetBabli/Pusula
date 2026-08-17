import React, { useState, useEffect } from 'react';
import CyberModal from '../ui/CyberModal';
import { Send, Building, ArrowLeft, CheckCircle2, AlertCircle } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';

function OutreachModal({ isOpen, onClose, onPrepare, onApprove }) {
  const { t } = useLanguage();
  const [step, setStep] = useState('form'); // 'form' | 'preview' | 'success'
  const [company, setCompany] = useState('');
  const [draft, setDraft] = useState(null);
  const [targetEmail, setTargetEmail] = useState('');
  const [preparing, setPreparing] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  // Sadece modal İLK AÇILDIĞINDA sıfırla (Kullanıcı iptal edip çıkmışsa eski veri kalmasın)
  useEffect(() => {
    if (isOpen) {
      setStep('form');
      setCompany('');
      setDraft(null);
      setTargetEmail('');
      setError(null);
    }
  }, [isOpen]);

  const handlePrepare = async (e) => {
    e.preventDefault();
    if (!company.trim() || preparing) return;
    setError(null);
    setPreparing(true);
    try {
      const result = await onPrepare(company.trim());
      setDraft(result);
      setTargetEmail(result.target_email);
      setStep('preview');
    } catch (err) {
      setError(err.message || t('outreach_modal_send'));
    } finally {
      setPreparing(false);
    }
  };

  const handleApprove = async () => {
    if (!draft || sending) return;
    setError(null);
    setSending(true);
    try {
      await onApprove(draft.id, targetEmail.trim());
      setStep('success');
    } catch (err) {
      setError(err.message || t('applications_send_failed_fallback'));
    } finally {
      setSending(false);
    }
  };

  return (
    <CyberModal isOpen={isOpen} onClose={onClose} title={t('outreach_modal_title')}>
      {step === 'form' && (
        <form onSubmit={handlePrepare} className="flex flex-col gap-4">
          <div className="flex items-start gap-3 p-4 rounded-md bg-primary-container/5 border border-primary-container/20 text-sm text-on-surface-variant" role="status" aria-live="polite">
            <Building className="w-5 h-5 text-primary shrink-0 mt-0.5" aria-hidden="true" />
            <p>{t('outreach_modal_info')}</p>
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
              disabled={preparing}
              required
              autoFocus
            />
          </fieldset>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label text-sm rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
            disabled={preparing || !company.trim()}
          >
            <Send className="w-4 h-4" aria-hidden="true" />
            {preparing ? t('outreach_modal_preparing') : t('outreach_modal_prepare_button')}
          </button>
        </form>
      )}

      {step === 'preview' && draft && (
        <div className="flex flex-col gap-4">
          <div className="flex items-start gap-3 p-4 rounded-md bg-primary-container/5 border border-primary-container/20 text-sm text-on-surface-variant" role="status" aria-live="polite">
            <Building className="w-5 h-5 text-primary shrink-0 mt-0.5" aria-hidden="true" />
            <p>{t('outreach_modal_review_hint')}</p>
          </div>

          <fieldset className="flex flex-col gap-2 border-none m-0 p-0">
            <label htmlFor="target-email" className="text-sm font-label text-on-surface-variant">{t('outreach_modal_target_email_label')}</label>
            <input
              id="target-email"
              type="email"
              className="bg-surface-container-lowest border border-outline-variant/10 text-sm text-on-surface rounded-md transition-colors duration-150 focus:ring-0 focus:border-primary/60 py-2.5 px-4"
              value={targetEmail}
              onChange={(e) => setTargetEmail(e.target.value)}
              disabled={sending}
              required
            />
          </fieldset>

          <div className="flex flex-col gap-1">
            <span className="text-sm font-label text-on-surface-variant">{t('outreach_modal_subject_label')}</span>
            <p className="text-sm text-on-surface bg-surface-container-lowest border border-outline-variant/10 rounded-md py-2.5 px-4">{draft.subject}</p>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-sm font-label text-on-surface-variant">{t('outreach_modal_body_label')}</span>
            <div className="text-sm text-on-surface-variant bg-surface-container-lowest border border-outline-variant/10 rounded-md py-2.5 px-4 max-h-48 overflow-y-auto whitespace-pre-wrap">
              {draft.body}
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setStep('form')}
              disabled={sending}
              className="flex items-center justify-center gap-2 py-3 px-4 bg-surface-container-highest hover:bg-surface-container-high text-on-surface font-label text-sm rounded-md transition-all duration-150 disabled:opacity-50"
            >
              <ArrowLeft className="w-4 h-4" aria-hidden="true" />
              {t('outreach_modal_back')}
            </button>
            <button
              type="button"
              onClick={handleApprove}
              disabled={sending || !targetEmail.trim()}
              className="flex-1 flex items-center justify-center gap-2 py-3 px-4 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white font-label text-sm rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
            >
              <Send className="w-4 h-4" aria-hidden="true" />
              {sending ? t('outreach_modal_sending') : t('outreach_modal_approve_send')}
            </button>
          </div>
        </div>
      )}

      {step === 'success' && (
        <div className="flex flex-col items-center gap-4 py-6 text-center">
          <CheckCircle2 className="w-10 h-10 text-emerald-500" aria-hidden="true" />
          <p className="text-sm text-on-surface">{t('outreach_modal_success')} <span className="text-on-surface-variant">({targetEmail})</span></p>
          <button
            type="button"
            onClick={onClose}
            className="py-2.5 px-6 bg-surface-container-highest hover:bg-surface-container-high text-on-surface font-label text-sm rounded-md transition-all duration-150"
          >
            {t('outreach_modal_close')}
          </button>
        </div>
      )}
    </CyberModal>
  );
}

export default OutreachModal;
