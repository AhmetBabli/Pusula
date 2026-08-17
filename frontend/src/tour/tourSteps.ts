// Tüm rehber tur adımları tek bu dosyadan yönetilir. Yeni bir adım eklemek
// için buraya bir satır eklemek yeterli — TourContext/TourOverlay hiçbir
// değişiklik gerektirmez. `target: null` olan adımlar (örn. karşılama) ekranın
// ortasında, spot ışığı olmadan gösterilir.
export interface TourStep {
  id: string;
  // Bu adım aktifken hangi sekmede olunmalı (Navigation.tsx / SIDEBAR_TABS ile birebir).
  tab: 'dashboard' | 'jobs' | 'applications' | 'events' | 'cv' | 'inbox' | 'agents';
  // Işıklandırılacak (spotlight) elementin CSS seçicisi. null ise ortalanmış gösterim.
  target: string | null;
  titleKey: string;
  descKey: string;
  placement: 'center' | 'right' | 'left' | 'top' | 'bottom';
}

export const TOUR_STEPS: TourStep[] = [
  { id: 'welcome', tab: 'dashboard', target: null, titleKey: 'tour_v2_welcome_title', descKey: 'tour_v2_welcome_desc', placement: 'center' },
  { id: 'dashboard', tab: 'dashboard', target: '#nav-tab-0', titleKey: 'tour_v2_dashboard_title', descKey: 'tour_v2_dashboard_desc', placement: 'right' },
  { id: 'jobs', tab: 'jobs', target: '#nav-tab-1', titleKey: 'tour_v2_jobs_title', descKey: 'tour_v2_jobs_desc', placement: 'right' },
  { id: 'applications', tab: 'applications', target: '#nav-tab-2', titleKey: 'tour_v2_applications_title', descKey: 'tour_v2_applications_desc', placement: 'right' },
  { id: 'events', tab: 'events', target: '#nav-tab-3', titleKey: 'tour_v2_events_title', descKey: 'tour_v2_events_desc', placement: 'right' },
  { id: 'cv', tab: 'cv', target: '#nav-tab-4', titleKey: 'tour_v2_cv_title', descKey: 'tour_v2_cv_desc', placement: 'right' },
  { id: 'inbox', tab: 'inbox', target: '#nav-tab-5', titleKey: 'tour_v2_inbox_title', descKey: 'tour_v2_inbox_desc', placement: 'right' },
  { id: 'agents', tab: 'agents', target: '#nav-tab-6', titleKey: 'tour_v2_agents_title', descKey: 'tour_v2_agents_desc', placement: 'right' },
  { id: 'done', tab: 'dashboard', target: null, titleKey: 'tour_v2_done_title', descKey: 'tour_v2_done_desc', placement: 'center' },
];

export const TOUR_STORAGE_KEY = 'pusula_tour_completed';
