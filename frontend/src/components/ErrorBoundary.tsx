import React, { ReactNode, ReactElement } from 'react';
import { AlertTriangle } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
}

function ErrorFallback({ error, errorInfo, onReset }: {
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  onReset: () => void;
}) {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-surface-container border border-error/30 rounded-lg p-8 text-center">
        <AlertTriangle className="w-12 h-12 text-error mx-auto mb-4" />

        <h1 className="text-2xl font-headline font-bold text-on-surface mb-2">{t('error_boundary_title')}</h1>
        <p className="text-on-surface-variant mb-6">
          {t('error_boundary_desc')}
        </p>

        {import.meta.env.DEV && error && (
          <div className="mb-6 text-left">
            <details className="text-sm">
              <summary className="cursor-pointer text-on-surface-variant hover:text-on-surface font-semibold mb-2">
                {t('error_boundary_details')}
              </summary>
              <div className="bg-surface-container-lowest p-4 rounded-md border border-outline-variant/10 overflow-auto max-h-48">
                <p className="text-error font-mono text-xs whitespace-pre-wrap">
                  {error.toString()}
                </p>
                {errorInfo && (
                  <p className="text-on-surface-variant font-mono text-xs mt-4 whitespace-pre-wrap">
                    {errorInfo.componentStack}
                  </p>
                )}
              </div>
            </details>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onReset}
            className="flex-1 px-4 py-2 bg-primary-container hover:bg-blue-700 active:scale-[0.98] text-white rounded-md font-semibold transition-all duration-150"
          >
            {t('error_boundary_refresh')}
          </button>
          <a
            href="/"
            className="flex-1 px-4 py-2 bg-surface-container-high hover:bg-surface-container-highest active:scale-[0.98] text-on-surface rounded-md font-semibold transition-all duration-150 text-center"
          >
            {t('error_boundary_home')}
          </a>
        </div>
      </div>
    </div>
  );
}

/**
 * Error Boundary Component for React
 * Catches and handles errors in child components gracefully
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    
    // Send to backend for monitoring (optional)
    this.logErrorToBackend(error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });
  }

  private logErrorToBackend = (error: Error, errorInfo: React.ErrorInfo) => {
    try {
      // Send error to backend logging endpoint
      fetch('/api/errors/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: error.toString(),
          stack: error.stack,
          componentStack: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        }),
      }).catch(err => console.error('Failed to log error to backend:', err));
    } catch (err) {
      console.error('Error logging failed:', err);
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactElement {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
        />
      );
    }

    return this.props.children as ReactElement;
  }
}
