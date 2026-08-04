import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LanguageProvider } from './i18n/LanguageContext'
import { ThemeProvider } from './contexts/ThemeContext'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error("Kritik Hata: 'root' id'li DOM elementi bulunamadı. Lütfen index.html dosyasını kontrol edin.")
}

createRoot(rootElement).render(
  <StrictMode>
    <ThemeProvider>
      <LanguageProvider>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </LanguageProvider>
    </ThemeProvider>
  </StrictMode>,
)