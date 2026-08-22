import React, { createContext, useContext, useState, useEffect, useMemo, useCallback, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const THEME_STORAGE_KEY = 'theme';

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function getInitialTheme(): Theme {
  // Pusula açık temayı varsayılan olarak kullanır (marka kararı) — sistem
  // tercihi burada kasıtlı olarak sorulmuyor, kullanıcı isterse üstteki
  // düğmeden kendi tercihini seçip kaydedebiliyor.
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return 'light';
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => setThemeState(next), []);
  const toggleTheme = useCallback(() => setThemeState((prev) => (prev === 'light' ? 'dark' : 'light')), []);

  const value = useMemo(() => ({ theme, setTheme, toggleTheme }), [theme, setTheme, toggleTheme]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
