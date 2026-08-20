import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Calendar, FileText, MessageSquare, Send, Compass, Terminal, Wifi, WifiOff, RotateCcw, Download, Activity, CheckCircle, AlertCircle, Mail, X, Info } from 'lucide-react';
import { useAgentWebSocket, AgentStates } from '../../hooks/useAgentWebSocket';
import { useLanguage, translateStatic } from '../../i18n/LanguageContext';
import { getToken } from '../../services/api';
import { InterviewCoach } from './InterviewCoach';

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

// ── Kısa Bilgilendirme Şeridi ───────────────────────────────────────────────
// Her araç ne yapar/ne yapmaz sorusunun cevabı, ilk bakışta görünsün diye
// başlığın hemen altında — sadece bir alt metin olarak değil, ayrı bir şerit.
function ToolInfoBanner({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2 text-xs font-body text-on-surface-variant bg-surface-container-lowest border border-outline-variant/10 rounded-md px-3 py-2.5">
      <Info className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
      <span>{text}</span>
    </div>
  );
}

// ── Kariyer Stratejisi Sonuç Görünümü ──────────────────────────────────────
function StrategyResults({ data, t }: { data: Record<string, any>; t: (k: string) => string }) {
  const market = data.market_overview || {};
  const gaps: any[] = data.skill_gap_analysis || [];
  const roadmap: any[] = data.roadmap_6_months || [];
  const projects: any[] = data.project_ideas || [];

  return (
    <div className="space-y-5 pt-2">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-surface-container-lowest border border-outline-variant/10 rounded-md p-3">
          <div className="text-xs text-on-surface-variant">{t('agents_strategy_salary_range')}</div>
          <div className="text-sm font-semibold text-on-surface mt-0.5">{market.salary_range || '—'}</div>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant/10 rounded-md p-3">
          <div className="text-xs text-on-surface-variant">{t('agents_strategy_demand_level')}</div>
          <div className="text-sm font-semibold text-on-surface mt-0.5">{market.demand_level || '—'}</div>
        </div>
      </div>

      {Array.isArray(market.top_technologies) && market.top_technologies.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {market.top_technologies.map((tech: string, i: number) => (
            <span key={i} className="px-2.5 py-1 rounded-md bg-primary-container/10 text-primary text-xs font-label">{tech}</span>
          ))}
        </div>
      )}

      {gaps.length > 0 && (
        <div>
          <div className="text-xs font-label font-semibold text-on-surface-variant mb-2">{t('agents_strategy_skill_gaps')}</div>
          <ul className="space-y-1.5">
            {gaps.map((g, i) => (
              <li key={i} className="text-sm text-on-surface-variant">
                <span className="text-on-surface font-medium">{g.skill}</span>
                {g.importance ? ` (${g.importance})` : ''} — {g.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {roadmap.length > 0 && (
        <div>
          <div className="text-xs font-label font-semibold text-on-surface-variant mb-2">{t('agents_strategy_roadmap')}</div>
          <div className="space-y-3">
            {roadmap.map((r, i) => (
              <div key={i} className="flex gap-3 text-sm">
                <span className="shrink-0 text-primary font-mono tabular-nums w-10">{r.month}</span>
                <div className="flex-1">
                  <div className="text-on-surface font-medium">{r.focus}</div>
                  {Array.isArray(r.actions) && (
                    <ul className="text-on-surface-variant text-xs mt-1 space-y-0.5">
                      {r.actions.map((a: string, j: number) => <li key={j}>• {a}</li>)}
                    </ul>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {projects.length > 0 && (
        <div>
          <div className="text-xs font-label font-semibold text-on-surface-variant mb-2">{t('agents_strategy_project_ideas')}</div>
          <div className="space-y-1.5">
            {projects.map((p, i) => (
              <div key={i} className="text-sm">
                <span className="text-on-surface font-medium">{p.title}</span>
                <span className="text-on-surface-variant"> — {p.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.final_advice && (
        <div className="text-sm italic text-on-surface-variant border-t border-outline-variant/10 pt-4">
          <span className="not-italic font-label font-semibold text-on-surface">{t('agents_strategy_final_advice')}: </span>
          {data.final_advice}
        </div>
      )}
    </div>
  );
}

// ── Sekme Tanımları ─────────────────────────────────────────────────────────
const TABS: { key: keyof AgentStates; icon: React.ElementType; titleKey: string }[] = [
  { key: 'web_search', icon: Search, titleKey: 'agents_research_title' },
  { key: 'event_search', icon: Calendar, titleKey: 'agents_events_title' },
  { key: 'cv_architect', icon: FileText, titleKey: 'agents_cv_title' },
  { key: 'outreach', icon: Send, titleKey: 'agents_outreach_title' },
  { key: 'strategy', icon: Compass, titleKey: 'agents_strategy_title' },
  { key: 'interview_coach', icon: MessageSquare, titleKey: 'agents_interview_title' },
];

const DOT_TONE: Record<string, string> = {
  running: 'bg-primary animate-pulse',
  done: 'bg-emerald-500',
  failed: 'bg-error',
};

// ── Ana Bileşen ────────────────────────────────────────────────────────────
export function AgentOrchestrator() {
  const { t } = useLanguage();
  const { agents, sessionId, connected, logs, resetAgent } = useAgentWebSocket();
  const [activeTab, setActiveTab] = useState<keyof AgentStates>('web_search');

  // Web Search state
  const [searchExpanded, setSearchExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLocation, setSearchLocation] = useState('İstanbul');

  // Event Search state
  const [eventsExpanded, setEventsExpanded] = useState(false);
  const [eventsQuery, setEventsQuery] = useState('');
  const [eventsLocation, setEventsLocation] = useState('İstanbul');

  // Outreach state
  const [outreachExpanded, setOutreachExpanded] = useState(false);
  const [outreachCompany, setOutreachCompany] = useState('');
  const [outreachResult, setOutreachResult] = useState<{ cold_email?: string; linkedin_dm?: string } | null>(null);

  // Strategy state
  const [strategyExpanded, setStrategyExpanded] = useState(false);
  const [strategyTargetJob, setStrategyTargetJob] = useState('');
  const [strategyTargetLocation, setStrategyTargetLocation] = useState('Global');

  const [actionError, setActionError] = useState<string | null>(null);
  const [showTerminal, setShowTerminal] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setActionError(null);
    try {
      await apiPost('/search', { query: searchQuery, location: searchLocation, session_id: sessionId });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleEventSearch = async () => {
    if (!eventsQuery.trim()) return;
    setActionError(null);
    try {
      await apiPost('/search-events', { query: eventsQuery, location: eventsLocation, session_id: sessionId });
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

  const handleStrategy = async () => {
    if (!strategyTargetJob.trim()) return;
    setActionError(null);
    try {
      await apiPost('/strategy', {
        session_id: sessionId,
        target_job: strategyTargetJob,
        target_location: strategyTargetLocation || 'Global',
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
    <div className="space-y-8 max-w-[1000px] mx-auto">
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

      {/* Sekme çubuğu */}
      <div className="flex gap-1.5 overflow-x-auto -mx-1 px-1 pb-2 border-b border-outline-variant/10">
        {TABS.map(tab => {
          const state = agents[tab.key];
          const isActive = activeTab === tab.key;
          const dotTone = DOT_TONE[state.status];
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-label transition-all duration-150 ${
                isActive
                  ? 'bg-primary-container/10 text-primary border border-primary-container/30'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest border border-transparent'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {t(tab.titleKey)}
              {dotTone && <span className={`w-1.5 h-1.5 rounded-full ${dotTone}`} />}
            </button>
          );
        })}
      </div>

      {/* Aktif sekme içeriği */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
          {activeTab === 'web_search' && (
            <AgentCard
              id="web_search" title={t('agents_research_title')} subtitle={t('agents_research_subtitle')}
              icon={Search}
              status={agents.web_search.status} step={agents.web_search.step}
              progress={agents.web_search.progress} data={agents.web_search.data}
              onReset={() => { resetAgent('web_search'); setSearchExpanded(false); }}
            >
              <ToolInfoBanner text={t('agents_research_info')} />
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
          )}

          {activeTab === 'event_search' && (
            <AgentCard
              id="event_search" title={t('agents_events_title')} subtitle={t('agents_events_subtitle')}
              icon={Calendar}
              status={agents.event_search.status} step={agents.event_search.step}
              progress={agents.event_search.progress} data={agents.event_search.data}
              onReset={() => { resetAgent('event_search'); setEventsExpanded(false); }}
            >
              <ToolInfoBanner text={t('agents_events_info')} />
              {agents.event_search.status === 'idle' && !eventsExpanded && (
                <button
                  onClick={() => setEventsExpanded(true)}
                  className="w-full py-3 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] transition-all duration-150"
                >
                  {t('agents_start_button')}
                </button>
              )}
              {agents.event_search.status === 'idle' && eventsExpanded && (
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    autoFocus
                    className="flex-[2] bg-surface-container-lowest border border-outline-variant/10 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150"
                    placeholder={t('agents_search_query_placeholder')}
                    value={eventsQuery}
                    onChange={e => setEventsQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleEventSearch()}
                  />
                  <input
                    className="flex-1 bg-surface-container-lowest border border-outline-variant/10 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150"
                    placeholder={t('agents_location_placeholder')}
                    value={eventsLocation}
                    onChange={e => setEventsLocation(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleEventSearch()}
                  />
                  <button
                    onClick={handleEventSearch}
                    disabled={!connected || !eventsQuery.trim()}
                    className="px-5 py-2.5 text-sm font-label bg-primary-container text-white rounded-md hover:bg-blue-700 active:scale-[0.97] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150"
                  >
                    {t('agents_search_button')}
                  </button>
                </div>
              )}
              {agents.event_search.status === 'done' && (
                <div className="text-sm text-on-surface-variant font-body">
                  <span className="text-on-surface font-semibold font-mono tabular-nums">{(agents.event_search.data?.saved_count as number) ?? 0}</span> {t('agents_events_found_suffix')}
                  {' '}{t('agents_review_in')}
                  <span className="text-primary hover:underline cursor-pointer font-medium transition-colors duration-150"> {t('nav_events')}</span>.
                </div>
              )}
            </AgentCard>
          )}

          {activeTab === 'cv_architect' && (
            <AgentCard
              id="cv_architect" title={t('agents_cv_title')} subtitle={t('agents_cv_subtitle')}
              icon={FileText}
              status={agents.cv_architect.status} step={agents.cv_architect.step}
              progress={agents.cv_architect.progress} data={agents.cv_architect.data}
              onReset={() => resetAgent('cv_architect')}
            >
              <ToolInfoBanner text={t('agents_cv_info')} />
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
          )}

          {activeTab === 'outreach' && (
            <AgentCard
              id="outreach" title={t('agents_outreach_title')} subtitle={t('agents_outreach_subtitle')}
              icon={Send}
              status={agents.outreach.status} step={agents.outreach.step}
              progress={agents.outreach.progress} data={agents.outreach.data}
              onReset={() => { resetAgent('outreach'); setOutreachResult(null); setOutreachExpanded(false); }}
            >
              <ToolInfoBanner text={t('agents_outreach_info')} />
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
          )}

          {activeTab === 'strategy' && (
            <AgentCard
              id="strategy" title={t('agents_strategy_title')} subtitle={t('agents_strategy_subtitle')}
              icon={Compass}
              status={agents.strategy.status} step={agents.strategy.step}
              progress={agents.strategy.progress} data={agents.strategy.data}
              onReset={() => { resetAgent('strategy'); setStrategyExpanded(false); }}
            >
              <ToolInfoBanner text={t('agents_strategy_info')} />
              {agents.strategy.status === 'idle' && !strategyExpanded && (
                <button
                  onClick={() => setStrategyExpanded(true)}
                  className="w-full py-3 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] transition-all duration-150"
                >
                  {t('agents_start_button')}
                </button>
              )}
              {agents.strategy.status === 'idle' && strategyExpanded && (
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    autoFocus
                    className="flex-[2] bg-surface-container-lowest border border-outline-variant/10 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150"
                    placeholder={t('agents_strategy_target_job_placeholder')}
                    value={strategyTargetJob}
                    onChange={e => setStrategyTargetJob(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleStrategy()}
                  />
                  <input
                    className="flex-1 bg-surface-container-lowest border border-outline-variant/10 rounded-md px-4 py-2.5 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors duration-150"
                    placeholder={t('agents_strategy_target_location_placeholder')}
                    value={strategyTargetLocation}
                    onChange={e => setStrategyTargetLocation(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleStrategy()}
                  />
                  <button
                    onClick={handleStrategy}
                    disabled={!connected || !strategyTargetJob.trim()}
                    className="px-5 py-2.5 text-sm font-label bg-primary-container text-white rounded-md hover:bg-blue-700 active:scale-[0.97] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150"
                  >
                    {t('agents_strategy_generate')}
                  </button>
                </div>
              )}
              {agents.strategy.status === 'done' && agents.strategy.data && Object.keys(agents.strategy.data).length > 0 && (
                <StrategyResults data={agents.strategy.data} t={t} />
              )}
            </AgentCard>
          )}

          {activeTab === 'interview_coach' && <InterviewCoach />}
        </motion.div>
      </AnimatePresence>

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
