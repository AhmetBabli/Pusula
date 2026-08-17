import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, User as UserIcon, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { login, register, loginWithGoogle } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

interface AuthUser {
  id: number;
  email: string;
  full_name: string;
}

interface AuthProps {
  onLogin: (user: AuthUser) => void;
}

const GOOGLE_CLIENT_ID = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID as string | undefined;
const GOOGLE_SCRIPT_ID = 'google-identity-script';

function loadGoogleScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if ((window as any).google?.accounts?.oauth2) {
      resolve();
      return;
    }
    const existing = document.getElementById(GOOGLE_SCRIPT_ID);
    if (existing) {
      existing.addEventListener('load', () => resolve());
      existing.addEventListener('error', () => reject(new Error('google-script-load-failed')));
      return;
    }
    const script = document.createElement('script');
    script.id = GOOGLE_SCRIPT_ID;
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('google-script-load-failed'));
    document.head.appendChild(script);
  });
}

const GoogleIcon = () => (
  <svg viewBox="0 0 48 48" className="w-4 h-4" aria-hidden="true">
    <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"/>
    <path fill="#FF3D00" d="M6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z"/>
    <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238C29.211 35.091 26.715 36 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"/>
    <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002 6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"/>
  </svg>
);

export const Auth: React.FC<AuthProps> = ({ onLogin }) => {
  const { t } = useLanguage();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    setError(null);
    setLoading(true);
    try {
      const data = mode === 'login'
        ? await login(email.trim(), password)
        : await register(email.trim(), password, fullName.trim());
      onLogin(data.user);
    } catch (err) {
      setError((err as Error).message || t('auth_generic_error'));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    if (loading) return;
    if (!GOOGLE_CLIENT_ID) {
      setError(t('auth_google_not_configured'));
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await loadGoogleScript();
      const google = (window as any).google;
      const client = google.accounts.oauth2.initCodeClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: 'openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly',
        ux_mode: 'popup',
        access_type: 'offline',
        prompt: 'consent',
        callback: async (response: any) => {
          try {
            if (!response?.code) throw new Error(t('auth_google_error'));
            const data = await loginWithGoogle(response.code);
            onLogin(data.user);
          } catch (err) {
            setError((err as Error).message || t('auth_google_error'));
          } finally {
            setLoading(false);
          }
        },
        error_callback: () => {
          setError(t('auth_google_error'));
          setLoading(false);
        },
      });
      client.requestCode();
    } catch (err) {
      setError((err as Error).message || t('auth_google_error'));
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface text-on-surface px-6 relative overflow-hidden">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="text-center mb-10 flex flex-col items-center">
          <div className="w-12 h-12 rounded-xl bg-primary-container/10 border border-primary-container/20 flex items-center justify-center mb-4">
            <ShieldCheck className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-2xl font-headline font-semibold tracking-wide text-on-surface mb-2">{t('app_title')}</h1>
          <p className="text-sm font-label text-on-surface-variant">
            {t('auth_subtitle')}
          </p>
        </div>

        <div className="bg-surface-container border border-outline-variant/10 rounded-2xl p-8 shadow-2xl backdrop-blur-sm relative overflow-hidden">

          {/* Top subtle highlight */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-outline-variant/20 to-transparent" />

          {/* Tabs */}
          <div className="flex w-full mb-8 relative">
            <button
              type="button"
              onClick={() => { setMode('login'); setError(null); }}
              className={`flex-1 pb-4 text-sm font-label transition-colors relative ${mode === 'login' ? 'text-on-surface' : 'text-on-surface-variant hover:text-on-surface/80'}`}
            >
              {t('auth_login_tab')}
            </button>
            <button
              type="button"
              onClick={() => { setMode('register'); setError(null); }}
              className={`flex-1 pb-4 text-sm font-label transition-colors relative ${mode === 'register' ? 'text-on-surface' : 'text-on-surface-variant hover:text-on-surface/80'}`}
            >
              {t('auth_register_tab')}
            </button>

            {/* Animated Underline */}
            <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-outline-variant/15" />
            <motion.div
              className="absolute bottom-0 h-[2px] bg-primary rounded-t-full shadow-[0_-2px_10px_rgba(37,99,235,0.5)]"
              initial={false}
              animate={{
                left: mode === 'login' ? '0%' : '50%',
                width: '50%'
              }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          </div>

          {/* Google ile Bağlan */}
          <div className="mb-6">
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              type="button"
              onClick={handleGoogleAuth}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2.5 py-3 bg-surface-container-highest hover:bg-surface-container-high border border-outline-variant/15 text-on-surface text-sm font-label rounded-xl transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <GoogleIcon />
              {t('auth_google_button')}
            </motion.button>
            {mode === 'register' && (
              <p className="text-xs text-on-surface-variant text-center mt-3 leading-relaxed">
                {t('auth_google_note')}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-outline-variant/15" />
            <span className="text-[11px] font-label text-on-surface-variant">{t('auth_divider_or')}</span>
            <div className="flex-1 h-px bg-outline-variant/15" />
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-error/10 border border-error/20 text-error text-sm mb-6">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <AnimatePresence mode="popLayout">
              <motion.div
                key={mode}
                initial={{ opacity: 0, x: mode === 'login' ? -20 : 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: mode === 'login' ? 20 : -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                {mode === 'register' && (
                  <div className="space-y-2">
                    <label htmlFor="auth-full-name" className="text-xs font-label font-medium text-on-surface-variant">{t('auth_full_name')}</label>
                    <div className="relative group">
                      <UserIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant group-focus-within:text-primary transition-colors" />
                      <input
                        id="auth-full-name"
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        disabled={loading}
                        className="w-full bg-surface-container-highest border border-outline-variant/15 rounded-xl py-3 pl-11 pr-4 text-sm text-on-surface font-body placeholder-on-surface-variant/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50"
                        placeholder={t('auth_full_name_placeholder')}
                      />
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <label htmlFor="auth-email" className="text-xs font-label font-medium text-on-surface-variant">{t('auth_email')}</label>
                  <div className="relative group">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant group-focus-within:text-primary transition-colors" />
                    <input
                      id="auth-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={loading}
                      className="w-full bg-surface-container-highest border border-outline-variant/15 rounded-xl py-3 pl-11 pr-4 text-sm text-on-surface font-body placeholder-on-surface-variant/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="auth-password" className="text-xs font-label font-medium text-on-surface-variant flex justify-between">
                    <span>{t('auth_password')}</span>
                  </label>
                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant group-focus-within:text-primary transition-colors" />
                    <input
                      id="auth-password"
                      type="password"
                      required
                      minLength={8}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={loading}
                      className="w-full bg-surface-container-highest border border-outline-variant/15 rounded-xl py-3 pl-11 pr-4 text-sm text-on-surface font-body placeholder-on-surface-variant/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="group w-full flex items-center justify-center gap-2 mt-8 py-3.5 bg-primary-container hover:bg-blue-700 text-white text-sm font-label rounded-xl transition-colors duration-300 shadow-lg shadow-primary-container/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? t('auth_waiting') : mode === 'login' ? t('auth_login_submit') : t('auth_register_submit')}
              {!loading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  );
};
