import React, { memo } from 'react';
import { User, Menu, X, Bell, Globe, Sun, Moon } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';
import { useTheme } from '../../contexts/ThemeContext';
import { LogoLockup } from '../ui/Logo';

function Header({ userProfile = {}, onProfileClick, isLoading, isSidebarOpen, onToggleSidebar }) {
  const { language, setLanguage, t } = useLanguage();
  const { theme, toggleTheme } = useTheme();

  const toggleLanguage = () => {
    setLanguage(language === 'tr' ? 'en' : 'tr');
  };

  return (
    <header className="h-16 w-full bg-surface-container/60 border-b border-outline-variant/10 backdrop-blur-xl flex items-center justify-between px-6 shrink-0 relative z-40">
      <div className="flex items-center gap-4">
        {/* Hamburger Menü Butonu */}
        <button
          className="p-2 rounded-md bg-outline-variant/5 hover:bg-outline-variant/10 active:scale-[0.96] text-on-surface transition-all duration-150 lg:hidden"
          onClick={onToggleSidebar}
          aria-label={isSidebarOpen ? t('header_close_menu') : t('header_open_menu')}
          aria-expanded={isSidebarOpen}
        >
          {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <LogoLockup wordmark={t('app_title')} tagline={t('app_subtitle')} />
      </div>

      <div className="flex items-center gap-2">
        {/* Tema Değiştirme Butonu */}
        <button
          onClick={toggleTheme}
          className="w-9 h-9 rounded-md bg-outline-variant/5 hover:bg-outline-variant/10 active:scale-[0.94] flex items-center justify-center text-on-surface transition-all duration-150"
          title={theme === 'dark' ? t('header_light_theme') : t('header_dark_theme')}
          aria-label={theme === 'dark' ? t('header_light_theme') : t('header_dark_theme')}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-primary" /> : <Moon className="w-4 h-4 text-primary" />}
        </button>

        {/* Dil Değiştirme Butonu */}
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-2 px-3 py-2 rounded-md bg-outline-variant/5 hover:bg-outline-variant/10 active:scale-[0.96] text-on-surface transition-all duration-150 border border-outline-variant/10"
          title={language === 'tr' ? 'Switch to English' : 'Türkçeye geç'}
        >
          <Globe className="w-4 h-4 text-primary" />
          <span className="text-xs font-label font-semibold tracking-wider uppercase">
            {language === 'tr' ? 'EN' : 'TR'}
          </span>
        </button>

        {/* Bildirimler */}
        <button className="w-9 h-9 rounded-md bg-outline-variant/5 hover:bg-outline-variant/10 active:scale-[0.94] flex items-center justify-center text-on-surface transition-all duration-150 relative">
          <Bell className="w-[18px] h-[18px]" />
          <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-primary ring-2 ring-surface animate-pulse" />
        </button>

        <div className="h-6 w-px bg-outline-variant/15 mx-1.5" />

        {/* Kullanıcı Profili */}
        <button
          className="flex items-center gap-3 px-3 py-1.5 rounded-md hover:bg-outline-variant/5 active:scale-[0.98] transition-all duration-150"
          onClick={() => onProfileClick('profile')}
        >
          <div className="text-right hidden md:block">
            <div className="text-sm font-label text-on-surface leading-tight">{t('my_profile')}</div>
            <div className="text-[10px] text-on-surface-variant">{t('admin')}</div>
          </div>
          <div className="w-8 h-8 rounded-full bg-primary-container/20 border border-primary/25 text-primary flex items-center justify-center">
            <User className="w-4 h-4" />
          </div>
        </button>
      </div>
    </header>
  );
}

export default memo(Header);
