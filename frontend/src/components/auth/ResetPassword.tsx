import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, ArrowRight, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react';
import { resetPassword } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

interface ResetPasswordProps {
  token: string;
  onDone: () => void;
}

export const ResetPassword: React.FC<ResetPasswordProps> = ({ token, onDone }) => {
  const { t } = useLanguage();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    if (newPassword !== confirmPassword) {
      setError(t('reset_password_mismatch_error'));
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await resetPassword(token, newPassword);
      setSuccess(true);
    } catch (err) {
      setError((err as Error).message || t('auth_generic_error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface text-on-surface px-6 relative overflow-hidden">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" as const }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="text-center mb-10 flex flex-col items-center">
          <div className="w-12 h-12 rounded-xl bg-primary-container/10 border border-primary-container/20 flex items-center justify-center mb-4">
            <ShieldCheck className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-2xl font-headline font-semibold tracking-wide text-on-surface mb-2">{t('app_title')}</h1>
          <p className="text-sm font-label text-on-surface-variant">{t('reset_password_title')}</p>
        </div>

        <div className="bg-surface-container border border-outline-variant/10 rounded-2xl p-8 shadow-2xl backdrop-blur-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-outline-variant/20 to-transparent" />

          {success ? (
            <div className="text-center py-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4 mx-auto">
                <CheckCircle2 className="w-6 h-6 text-emerald-500" />
              </div>
              <p className="text-sm font-body text-on-surface-variant leading-relaxed mb-6">{t('reset_password_success')}</p>
              <button
                type="button"
                onClick={onDone}
                className="text-sm font-label text-primary hover:underline"
              >
                {t('auth_back_to_login')}
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-error/10 border border-error/20 text-error text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="reset-new-password" className="text-xs font-label font-medium text-on-surface-variant">
                  {t('reset_password_new_label')}
                </label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant group-focus-within:text-primary transition-colors" />
                  <input
                    id="reset-new-password"
                    type="password"
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    disabled={loading}
                    className="w-full bg-surface-container-highest border border-outline-variant/15 rounded-xl py-3 pl-11 pr-4 text-sm text-on-surface font-body placeholder-on-surface-variant/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="reset-confirm-password" className="text-xs font-label font-medium text-on-surface-variant">
                  {t('reset_password_confirm_label')}
                </label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant group-focus-within:text-primary transition-colors" />
                  <input
                    id="reset-confirm-password"
                    type="password"
                    required
                    minLength={8}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={loading}
                    className="w-full bg-surface-container-highest border border-outline-variant/15 rounded-xl py-3 pl-11 pr-4 text-sm text-on-surface font-body placeholder-on-surface-variant/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                className="group w-full flex items-center justify-center gap-2 mt-2 py-3.5 bg-primary-container hover:bg-blue-700 text-white text-sm font-label rounded-xl transition-colors duration-300 shadow-lg shadow-primary-container/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? t('auth_waiting') : t('reset_password_submit')}
                {!loading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
              </motion.button>
            </form>
          )}
        </div>
      </motion.div>
    </div>
  );
};
