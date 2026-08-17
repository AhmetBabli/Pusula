import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, FileText, MessageSquare, Send, Terminal, Wifi, WifiOff, RotateCcw, Download, Activity, CheckCircle, AlertCircle, Mail, X } from 'lucide-react';
import { useAgentWebSocket, AgentStates } from '../../hooks/useAgentWebSocket';
import { useLanguage, translateStatic } from '../../i18n/LanguageContext';
import { getToken } from '../../services/api';

// ── API Çağrıları ──────────────────────────────────────────────────────────
const API = '/api/agents';

async function apiPost(path: string, body: object) {
  const token = getToken() || '';
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || data.message || `${translateStatic('common_request_failed')} (${res.status})`);
  }
  return data;
}

// ── Ajan Kart Bileşeni ─────────────────────────────────────────────────────
interface AgentCardProps {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  status: string;
  step: string;
  progress: number;
  data: Record<string, unknown>;
  onReset: () => void;
  children: React.ReactNode;
}

function AgentCard({ title, subtitle, icon: Icon, status, step, progress, onReset, children }: AgentCardProps) {
  const { t } = useLanguage();
  const isRunning = status === 'running';
  const isDone = status === 'done';
  const isFailed = status === 'failed';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`bg-surface-container border rounded-xl p-7 flex flex-col gap-5 transition-all duration-150 relative overflow-hidden
      ${isRunning ? 'border-primary-container' :
        isDone ? 'border-emerald-500/30' :
          isFailed ? 'border-error/30' :
            'border-outline-variant/10 hover:border-outline-variant/20'}`}
    >
      {isRunning && (
        <div className="absolute top-0 left-0 w-full h-1 bg-surface-container-highest">
          <motion.div
            className="h-full bg-primary-container"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ ease: "linear" }}
          />
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-lg flex items-center justify-center bg-primary/10 text-primary shrink-0">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <div className="text-base font-headline font-semibold text-on-surface">{title}</div>
            <div className="text-xs text-on-surface-variant mt-1">{subtitle}</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {isRunning && (
            <div className="flex items-center gap-2 text-xs font-label text-primary bg-primary-container/10 px-3 py-1 rounded-md border border-primary-container/20">
              <Activity className="w-3.5 h-3.5 animate-spin" /> {t('agents_status_running')}
            </div>
          )}
          {isDone && (
            <div className="flex items-center gap-2 text-xs font-label text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-md border border-emerald-500/20">
              <CheckCircle className="w-3.5 h-3.5" /> {t('agents_status_complete')}
            </div>
          )}
          {isFailed && (
            <div className="flex items-center gap-2 text-xs font-label text-error bg-error/10 px-3 py-1 rounded-md border border-error/20">
              <AlertCircle className="w-3.5 h-3.5" /> {t('agents_status_failed')}
            </div>
          )}

          {(isDone || isFailed) && (
            <button onClick={onReset} className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-container-highest active:scale-[0.94] text-on-surface-variant hover:text-on-surface transition-all duration-150" title={t('agents_reset_title')}>
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Status Label for Running */}
      {isRunning && step && (
        <div className="text-sm font-body text-on-surface-variant animate-pulse">{step}</div>
      )}
      {isFailed && step && (
        <div className="text-sm font-body text-error line-clamp-2">{step}</div>
      )}

      {/* Action content */}
      <div className="mt-auto pt-5 border-t border-outline-variant/10">
        {children}
      </div>
    </motion.div>
  );
}

// ── Ana Bileşen ────────────────────────────────────────────────────────────
export function AgentOrchestrator() {
  const { t } = useLanguage();
  const { agents, sessionId, connected, logs, resetAgent } = useAgentWebSocket();

  // Web Search state
  const [searchExpanded, setSearchExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLocation, setSearchLocation] = useState('İstanbul');

  // Outreach state
  const [outreachExpanded, setOutreachExpanded] = useState(false);
  const [outreachCompany, setOutreachCompany] = useState('');
  const [outreachResult, setOutreachResult] = useState<{ cold_email?: string; linkedin_dm?: string } | null>(null);

  // CV Architect
  const [showTerminal, setShowTerminal] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setActionError(null);
    try {
      await apiPost('/search', { query: searchQuery, location: searchLocation, session_id: sessionId });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleBuildCv = async () => {
    setActionError(null);
    try {
      await apiPost('/build-cv', { session_id: sessionId });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleDownloadCv = async (cvSessionId: string) => {
    setActionError(null);
    try {
      const token = getToken() || '';
      const res = await fetch(`${API}/cv/export-pdf/${cvSessionId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `PDF indirilemedi (${res.status})`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kariyer_cv_${cvSessionId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleOutreach = async () => {
    if (!outreachCompany.trim()) return;
    setActionError(null);
    try {
      await apiPost('/outreach', {
        session_id: sessionId,
        company_name: outreachCompany,
      });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  // Outreach data gelince göster
  React.useEffect(() => {
    const d = agents.outreach.data;
    if (agents.outreach.status === 'done' && d?.cold_email) {
      setOutreachResult({ cold_email: d.cold_email as string, linkedin_dm: d.linkedin_dm as string });
    }
  }, [agents.outreach]);

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto">
      {/* Header */}
      <motion.header initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="font-headline text-3xl md:text-4xl text-on-surface mb-2 font-bold tracking-tight">{t('agents_title')}</h2>
          <p className="font-body text-base text-on-surface-variant">{t('agents_subtitle')}</p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-label font-medium w-fit ${connected ? 'text-emerald-500' : 'text-error'}`}>
          {connected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
          {connected ? t('agents_connected') : t('agents_disconnected')}
        </div>
      </motion.header>

      <AnimatePresence>
        {actionError && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="flex-1">{actionError}</span>
            <button onClick={() => setActionError(null)} className="shrink-0 hover:opacity-70" aria-label="Kapat">
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 4 Ajan Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* 1. Web Search Agent */}
        <AgentCard
          id="web_search" title={t('agents_research_title')} subtitle={t('agents_research_subtitle')}
          icon={Search}
          status={agents.web_search.status} step={agents.web_search.step}
          progress={agents.web_search.progress} data={agents.web_search.data}
          onReset={() => { resetAgent('web_search'); setSearchExpanded(false); }}
        >
          {agents.web_search.status === 'idle' && !searchExpanded && (
            <button
              onClick={() => setSearchExpanded(true)}
              className="w-full py-3 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] transition-all duration-150"
            >
              {t('agents_start_button')}
            </button>
          )}
          {agents.web_search.status === 'idle' && searchExpanded && (
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                autoFocus
                className="flex-[2] bg-surface-container-lowest border border-outline-variant/10 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150"
                placeholder={t('agents_search_query_placeholder')}
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
              <input
                className="flex-1 bg-surface-container-lowest border border-outline-variant/10 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150"
                placeholder={t('agents_location_placeholder')}
                value={searchLocation}
                onChange={e => setSearchLocation(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
              <button
                onClick={handleSearch}
                disabled={!connected || !searchQuery.trim()}
                className="px-5 py-2.5 text-sm font-label bg-primary-container text-white rounded-md hover:bg-blue-700 active:scale-[0.97] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150"
              >
                {t('agents_search_button')}
              </button>
            </div>
          )}
          {agents.web_search.status === 'done' && (
            <div className="text-sm text-on-surface-variant font-body">
              <span className="text-on-surface font-semibold font-mono tabular-nums">{(agents.web_search.data?.saved_count as number) ?? 0}</span> {t('agents_jobs_found_suffix')}
              {' '}{t('agents_review_in')}
              <span className="text-primary hover:underline cursor-pointer font-medium transition-colors duration-150"> {t('nav_market_analysis')}</span>.
            </div>
          )}
        </AgentCard>

        {/* 2. CV Architect Agent */}
        <AgentCard
          id="cv_architect" title={t('agents_cv_title')} subtitle={t('agents_cv_subtitle')}
          icon={FileText}
          status={agents.cv_architect.status} step={agents.cv_architect.step}
          progress={agents.cv_architect.progress} data={agents.cv_architect.data}
          onReset={() => resetAgent('cv_architect')}
        >
          {agents.cv_architect.status === 'idle' && (
            <button
              onClick={handleBuildCv}
              disabled={!connected}
              className="w-full py-3 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150"
            >
              {t('agents_cv_start_button')}
            </button>
          )}
          {agents.cv_architect.status === 'done' && agents.cv_architect.data?.session_id && (
            <button
              onClick={() => handleDownloadCv(agents.cv_architect.data.session_id as string)}
              className="w-full flex items-center justify-center gap-2 py-3 text-sm font-label text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 rounded-md hover:bg-emerald-500/20 active:scale-[0.98] transition-all duration-150"
            >
              <Download className="w-4 h-4" /> {t('agents_cv_download')}
            </button>
          )}
        </AgentCard>

        {/* 3. Mülakat Koçu */}
        <AgentCard
          id="interview_coach" title={t('agents_interview_title')} subtitle={t('agents_interview_subtitle')}
          icon={MessageSquare}
          status={agents.interview_coach.status} step={agents.interview_coach.step}
          progress={agents.interview_coach.progress} data={agents.interview_coach.data}
          onReset={() => resetAgent('interview_coach')}
        >
          <a
            href="#interview"
            className="w-full flex items-center justify-center py-3 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] transition-all duration-150"
          >
            {t('agents_interview_open')}
          </a>
        </AgentCard>

        {/* 4. İletişim Asistanı */}
        <AgentCard
          id="outreach" title={t('agents_outreach_title')} subtitle={t('agents_outreach_subtitle')}
          icon={Send}
          status={agents.outreach.status} step={agents.outreach.step}
          progress={agents.outreach.progress} data={agents.outreach.data}
          onReset={() => { resetAgent('outreach'); setOutreachResult(null); setOutreachExpanded(false); }}
        >
          {agents.outreach.status === 'idle' && !outreachExpanded && (
            <button
              onClick={() => setOutreachExpanded(true)}
              className="w-full py-3 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] transition-all duration-150"
            >
              {t('agents_start_button')}
            </button>
          )}
          {agents.outreach.status === 'idle' && outreachExpanded && (
            <div className="flex gap-3">
              <input
                autoFocus
                className="flex-1 bg-surface-container-lowest border border-outline-variant/10 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150"
                placeholder={t('agents_outreach_company_placeholder')}
                value={outreachCompany}
                onChange={e => setOutreachCompany(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleOutreach()}
              />
              <button
                onClick={handleOutreach}
                disabled={!connected || !outreachCompany.trim()}
                className="px-5 py-2.5 text-sm font-label bg-primary-container text-white rounded-md hover:bg-blue-700 active:scale-[0.97] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150"
              >
                {t('agents_outreach_generate')}
              </button>
            </div>
          )}
          {outreachResult && (
            <div className="space-y-3 pt-2">
              <div className="bg-surface-container-lowest border border-outline-variant/10 rounded-md p-4">
                <div className="text-xs font-label font-semibold text-primary mb-2 flex items-center gap-1.5"><Mail className="w-3.5 h-3.5"/> {t('agents_outreach_email_draft')}</div>
                <pre className="text-sm font-body text-on-surface-variant whitespace-pre-wrap leading-relaxed">
                  {outreachResult.cold_email}
                </pre>
              </div>
              {outreachResult.linkedin_dm && (
                <div className="bg-surface-container-lowest border border-outline-variant/10 rounded-md p-4">
                  <div className="text-xs font-label font-semibold text-primary mb-2 flex items-center gap-1.5"><MessageSquare className="w-3.5 h-3.5"/> {t('agents_outreach_linkedin_draft')}</div>
                  <pre className="text-sm font-body text-on-surface-variant whitespace-pre-wrap leading-relaxed">
                    {outreachResult.linkedin_dm}
                  </pre>
                </div>
              )}
            </div>
          )}
        </AgentCard>
      </div>

      {/* Terminal Log */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2, duration: 0.25 }} className="pt-8 border-t border-outline-variant/10">
        <button
          onClick={() => setShowTerminal(p => !p)}
          className="flex items-center gap-2 text-sm font-label text-on-surface-variant hover:text-on-surface transition-colors duration-150 mb-4"
        >
          <Terminal className="w-4 h-4" />
          {showTerminal ? t('agents_log_hide') : t('agents_log_show')}
          <span className="bg-surface-container-highest px-2 py-0.5 rounded text-xs font-mono tabular-nums">{logs.length} {t('agents_log_entries_suffix')}</span>
        </button>
        <AnimatePresence>
          {showTerminal && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="bg-surface-container-lowest border border-outline-variant/10 rounded-md p-5 h-64 overflow-y-auto font-mono text-[13px] text-on-surface-variant space-y-1.5"
            >
              {logs.length === 0 && <div className="text-on-surface-variant/40">{t('agents_log_empty')}</div>}
              {logs.map((l, i) => <div key={i} className="leading-snug">
                <span className="text-primary/50 mr-2">[{new Date().toISOString().substring(11,19)}]</span> {l}
              </div>)}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
