import React, { useState, useEffect } from 'react';
import { Code2, Sun, Moon, Globe } from 'lucide-react';
import { useLanguage } from './i18n/LanguageContext';
import { useTheme } from './contexts/ThemeContext';

import { LoadingScreen } from './components/onboarding/LoadingScreen';
import { Onboarding } from './components/onboarding/Onboarding';
import { FeatureTour } from './components/onboarding/FeatureTour';
import { ProfileIntake } from './components/onboarding/ProfileIntake';
import { Auth } from './components/auth/Auth';
import { ProfileView, UserProfile } from './components/dashboard/ProfileView';
import { AgentOrchestrator } from './components/agents/AgentOrchestrator';
import { InterviewCoach } from './components/agents/InterviewCoach';
import DashboardView from './components/dashboard/DashboardView';
import JobsView from './components/jobs/JobsView';
import ApplicationsView from './components/applications/ApplicationsView';
import EventsView from './components/events/EventsView';
import CVView from './components/cv/CVView';
import InboxView from './components/inbox/InboxView';
import GmailModal from './components/modals/GmailModal';
import OutreachModal from './components/modals/OutreachModal';
import Header from './components/layout/Header';
import Navigation from './components/layout/Navigation';
import { useTaskStream } from './hooks/useTaskStream';
import {
  getDashboardStats, getJobs, getApplications, getEvents, getCVs, getInboxItems,
  syncJobs, syncInbox, prepareApplication, approveApplication, submitApplication,
  uploadCV, deleteCV, setDefaultCV, linkEmailAccount, sendColdEmail,
  getProfile, getToken, logout as apiLogout,
} from './services/api';

type Tab = 'dashboard' | 'jobs' | 'applications' | 'events' | 'cv' | 'inbox' | 'profile' | 'agents';
type AppState = 'loading' | 'onboarding' | 'auth' | 'tour' | 'intake' | 'dashboard';

// Sıra, Navigation.tsx'in sabit 7 bölümüyle (Dashboard/Pazar Analizi/Başvurular/
// Etkinlikler/Portföy/Gelen Kutusu/Ajan Merkezi) birebir eşleşmeli.
const SIDEBAR_TABS: Tab[] = ['dashboard', 'jobs', 'applications', 'events', 'cv', 'inbox', 'agents'];

/* ── GLOBAL FOOTER ── */
const Footer = () => {
  const { t } = useLanguage();
  return (
    <footer className="absolute bottom-0 left-0 w-full py-4 text-center z-50 pointer-events-none">
      <p className="text-xs text-gray-600">
        © 2026 Ahmet Babli Çulcu. {t('app_footer_rights')}
      </p>
    </footer>
  );
};

/* ── KAYIT/GİRİŞ AKIŞI İÇİN KÖK SEVİYE DİL + TEMA DÜĞMESİ ──
   Header sadece Dashboard'da mevcut olduğundan, onboarding/auth/tour/intake
   ekranlarında da dil ve tema değiştirilebilsin diye buraya eklendi. */
const CornerControls = () => {
  const { language, setLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  return (
    <div className="fixed top-4 right-4 z-50 flex items-center gap-2">
      <button
        onClick={toggleTheme}
        className="w-9 h-9 rounded-md bg-surface-container/80 hover:bg-surface-container-high border border-outline-variant/15 backdrop-blur-xl flex items-center justify-center text-on-surface transition-all duration-150"
        title={theme === 'dark' ? 'Açık temaya geç' : 'Koyu temaya geç'}
      >
        {theme === 'dark' ? <Sun className="w-4 h-4 text-primary" /> : <Moon className="w-4 h-4 text-primary" />}
      </button>
      <button
        onClick={() => setLanguage(language === 'tr' ? 'en' : 'tr')}
        className="flex items-center gap-1.5 px-3 py-2 rounded-md bg-surface-container/80 hover:bg-surface-container-high border border-outline-variant/15 backdrop-blur-xl text-on-surface transition-all duration-150"
        title={language === 'tr' ? 'Switch to English' : 'Türkçeye geç'}
      >
        <Globe className="w-4 h-4 text-primary" />
        <span className="text-xs font-label font-semibold tracking-wider uppercase">{language === 'tr' ? 'EN' : 'TR'}</span>
      </button>
    </div>
  );
};

/* ── APP ROOT ── */
const App: React.FC = () => {
  const { t } = useLanguage();
  const [appState, setAppState] = useState<AppState>('loading');
  const [tab, setTab] = useState<Tab>('dashboard');
  const [sideOpen, setSideOpen] = useState(false);
  const [isDevView, setIsDevView] = useState(false);

  // Otonom Sistem: Kullanıcı profili verisi
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  // Sayfa verileri
  const [dashboardStats, setDashboardStats] = useState<any>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [jobs, setJobs] = useState<any[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [applications, setApplications] = useState<any[]>([]);
  const [applicationsLoading, setApplicationsLoading] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [cvs, setCvs] = useState<any[]>([]);
  const [cvsLoading, setCvsLoading] = useState(false);
  const [inboxItems, setInboxItems] = useState<any[]>([]);
  const [inboxLoading, setInboxLoading] = useState(false);

  // Modaller
  const [gmailModalOpen, setGmailModalOpen] = useState(false);
  const [gmailLinking, setGmailLinking] = useState(false);
  const [outreachModalOpen, setOutreachModalOpen] = useState(false);
  const [outreachSending, setOutreachSending] = useState(false);

  const { task: syncTask, startTracking } = useTaskStream();

  const refreshDashboard = async () => {
    setStatsLoading(true);
    try {
      const data = await getDashboardStats();
      setDashboardStats(data);
    } catch (err) {
      console.error('Dashboard stats error:', err);
    } finally {
      setStatsLoading(false);
    }
  };

  const refreshJobs = async () => {
    setJobsLoading(true);
    try {
      const data = await getJobs();
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Jobs fetch error:', err);
    } finally {
      setJobsLoading(false);
    }
  };

  const refreshApplications = async () => {
    setApplicationsLoading(true);
    try {
      const data = await getApplications(undefined);
      setApplications(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Applications fetch error:', err);
    } finally {
      setApplicationsLoading(false);
    }
  };

  const refreshEvents = async () => {
    setEventsLoading(true);
    try {
      const data = await getEvents();
      // Backend EventOut sadece `source_url` döndürüyor; EventsView `event.url` okuyor.
      setEvents(Array.isArray(data) ? data.map((e: any) => ({ ...e, url: e.source_url })) : []);
    } catch (err) {
      console.error('Events fetch error:', err);
    } finally {
      setEventsLoading(false);
    }
  };

  const refreshCvs = async () => {
    setCvsLoading(true);
    try {
      const data = await getCVs();
      setCvs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('CVs fetch error:', err);
    } finally {
      setCvsLoading(false);
    }
  };

  const refreshInbox = async () => {
    setInboxLoading(true);
    try {
      const data = await getInboxItems();
      setInboxItems(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Inbox fetch error:', err);
    } finally {
      setInboxLoading(false);
    }
  };

  const loadProfileAndEnterDashboard = async () => {
    try {
      const profile = await getProfile();
      setUserProfile(profile);
      setAppState(profile?.onboarding_completed ? 'dashboard' : 'tour');
    } catch (err) {
      console.error('Oturum doğrulanamadı:', err);
      apiLogout();
      setAppState((prev) => (prev === 'dashboard' ? 'auth' : prev));
    }
  };

  // Sayfa yüklendiğinde saklı bir oturum token'ı varsa doğrudan Dashboard'a geç
  useEffect(() => {
    if (getToken()) {
      loadProfileAndEnterDashboard();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (appState !== 'dashboard') return;
    refreshDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appState]);

  useEffect(() => {
    if (tab === 'jobs' && jobs.length === 0) refreshJobs();
    else if (tab === 'applications' && applications.length === 0) refreshApplications();
    else if (tab === 'events' && events.length === 0) refreshEvents();
    else if (tab === 'cv' && cvs.length === 0) refreshCvs();
    else if (tab === 'inbox' && inboxItems.length === 0) refreshInbox();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  useEffect(() => {
    if (syncTask.status === 'done') {
      refreshJobs();
      refreshDashboard();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [syncTask.status]);

  const handleDeepScan = async () => {
    try {
      const res = await syncJobs();
      if (res?.task_id) startTracking(res.task_id);
    } catch (err) {
      console.error('Deep scan error:', err);
    }
  };

  const handleSyncInbox = async () => {
    setInboxLoading(true);
    try {
      await syncInbox();
      await refreshInbox();
    } catch (err) {
      console.error('Inbox sync error:', err);
    } finally {
      setInboxLoading(false);
    }
  };

  const handleJobAction = async (action: string, jobId: number) => {
    if (action !== 'prepare') return;
    try {
      await prepareApplication(jobId);
      setTab('applications');
      await refreshApplications();
    } catch (err) {
      console.error('Prepare application error:', err);
    }
  };

  const handleApprove = async (id: number, approved: boolean, contactEmail?: string) => {
    try {
      await approveApplication(id, approved, null, contactEmail ?? null);
      await refreshApplications();
      await refreshDashboard();
    } catch (err) {
      console.error('Approve application error:', err);
    }
  };

  const handleSubmitApplication = async (id: number) => {
    try {
      await submitApplication(id);
    } catch (err) {
      // Gönderim başarısız olsa da backend send_status/send_error'ı zaten kaydetti —
      // aşağıdaki refresh bu durumu arayüze yansıtacak (kullanıcı "Tekrar Dene" görecek).
      console.error('Submit application error:', err);
    } finally {
      await refreshApplications();
      await refreshDashboard();
    }
  };

  const handleCvUpload = async (file: File, title: string, variant: string) => {
    await uploadCV(file, title, variant);
    await refreshCvs();
  };

  const handleCvDelete = async (id: number) => {
    await deleteCV(id);
    await refreshCvs();
  };

  const handleCvSetDefault = async (id: number) => {
    await setDefaultCV(id);
    await refreshCvs();
  };

  const handleLinkGmail = async (email: string, appPassword: string) => {
    setGmailLinking(true);
    try {
      await linkEmailAccount(email, appPassword);
      setGmailModalOpen(false);
    } finally {
      setGmailLinking(false);
    }
  };

  const handleLogout = () => {
    apiLogout();
    setUserProfile(null);
    setTab('dashboard');
    setAppState('auth');
    // Bir sonraki kullanıcı öncekinin verisini görmesin diye önbelleği temizle
    setDashboardStats(null);
    setJobs([]);
    setApplications([]);
    setEvents([]);
    setCvs([]);
    setInboxItems([]);
  };

  const handleSendOutreach = async (companyName: string) => {
    setOutreachSending(true);
    try {
      await sendColdEmail(companyName);
      setOutreachModalOpen(false);
    } finally {
      setOutreachSending(false);
    }
  };

  const isSyncing = syncTask.status === 'running' || syncTask.status === 'pending';

  const views: Record<Tab, React.ReactNode> = {
    dashboard: (
      <DashboardView
        stats={dashboardStats || {}}
        isLoading={statsLoading || isSyncing}
        onDeepScan={handleDeepScan}
        onSyncInbox={handleSyncInbox}
        onOpenGmail={() => setGmailModalOpen(true)}
        onOpenOutreach={() => setOutreachModalOpen(true)}
        onOpenJobs={() => setTab('jobs')}
        onOpenApplications={() => setTab('applications')}
      />
    ),
    jobs: <JobsView jobs={jobs} isLoading={jobsLoading} onJobAction={handleJobAction} />,
    applications: (
      <ApplicationsView
        applications={applications}
        isLoading={applicationsLoading}
        onApprove={handleApprove}
        onSubmit={handleSubmitApplication}
      />
    ),
    events: <EventsView events={events} isLoading={eventsLoading} />,
    cv: (
      <CVView
        cvs={cvs}
        isLoading={cvsLoading}
        onUpload={handleCvUpload}
        onDelete={handleCvDelete}
        onSetDefault={handleCvSetDefault}
      />
    ),
    inbox: <InboxView items={inboxItems} isLoading={inboxLoading} onSync={handleSyncInbox} />,
    profile: <ProfileView userProfile={userProfile} onSave={setUserProfile} onLogout={handleLogout} />,
    agents: (
      <div className="space-y-10">
        <AgentOrchestrator />
        <div className="border-t border-outline-variant/10 pt-8">
          <div className="text-[10px] font-mono text-on-surface-variant tracking-[0.2em] mb-6">{t('app_interview_simulator_label')}</div>
          <InterviewCoach />
        </div>
      </div>
    ),
  };

  // Determine which state to show based on dev toggle
  const currentState = isDevView ? 'dashboard' : appState;

  // State Yönetimi ile Ekran Render
  const renderContent = () => {
    switch (currentState) {
      case 'loading':
        return <LoadingScreen onComplete={() => setAppState('onboarding')} />;
      case 'onboarding':
        return <Onboarding onComplete={() => setAppState('auth')} />;
      case 'auth':
        // Giriş/kayıt başarılı olunca gerçek profili çekip Dashboard'a (veya ilk kayıtsa tanıtıma) geç
        return <Auth onLogin={() => loadProfileAndEnterDashboard()} />;
      case 'tour':
        return <FeatureTour onComplete={() => setAppState('intake')} />;
      case 'intake':
        return <ProfileIntake onComplete={() => loadProfileAndEnterDashboard()} />;
      case 'dashboard':
        return (
          <div className="min-h-screen bg-surface text-on-surface font-sans flex overflow-hidden">
            {/* Mobile overlay */}
            {sideOpen && <div className="fixed inset-0 bg-surface-dim/60 z-30 lg:hidden" onClick={()=>setSideOpen(false)}/>}

            {/* Sidebar */}
            <aside className={`fixed lg:static top-0 left-0 h-full z-40 shrink-0 transition-transform duration-300 ${sideOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
              <Navigation
                activeIndex={SIDEBAR_TABS.indexOf(tab)}
                onChange={(idx: number) => { setTab(SIDEBAR_TABS[idx]); setSideOpen(false); }}
                isAuthenticated={true}
              />
            </aside>

            {/* Main */}
            <div className="flex-1 flex flex-col min-h-screen overflow-auto relative z-10">
              {/* Topbar */}
              <Header
                userProfile={userProfile || {}}
                onProfileClick={(action) => setTab('profile')}
                isLoading={false}
                isSidebarOpen={sideOpen}
                onToggleSidebar={() => setSideOpen(!sideOpen)}
              />

              {/* Page */}
              <main className="flex-1 px-6 py-8 md:p-10 w-full max-w-[1400px] mx-auto pb-20">
                <div key={tab} style={{animation:'fadeIn 0.3s ease'}}>
                  {views[tab]}
                </div>
              </main>
            </div>

            <GmailModal
              isOpen={gmailModalOpen}
              onClose={() => setGmailModalOpen(false)}
              onLink={handleLinkGmail}
              isLoading={gmailLinking}
            />
            <OutreachModal
              isOpen={outreachModalOpen}
              onClose={() => setOutreachModalOpen(false)}
              onSend={handleSendOutreach}
              isLoading={outreachSending}
            />
          </div>
        );
    }
  };

  return (
    <div className="relative min-h-screen bg-surface">
      {currentState !== 'dashboard' && <CornerControls />}
      {renderContent()}
      <Footer />

      {/* DEV Toggle Button */}
      <button
        onClick={() => setIsDevView(!isDevView)}
        className="fixed bottom-4 right-4 z-50 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 rounded px-2 py-1 flex items-center gap-1 transition-all"
        title="Geliştirici Modu: Akışı Atla"
      >
        <Code2 className="w-3 h-3" />
        <span className="text-[9px] font-mono uppercase tracking-widest">{isDevView ? 'Dev: Off' : 'Dev: On'}</span>
      </button>

      <style>{`@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}`}</style>
    </div>
  );
};

export default App;
