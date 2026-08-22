// Uygulama genelinde sekme (tab) tipi. App.tsx (sidebar/router) ve
// tour/TourContext.tsx (tur adımlarının hangi sekmeye navigate edeceği) aynı
// tipi paylaşmalı — ayrı ayrı tanımlanmaları (biri 9, diğeri 7 üye) TS2719
// "iki farklı Tab tipi" çakışmasına ve turun yeni sekmelere (interview,
// profile) sessizce kör kalmasına yol açıyordu.
export type Tab =
  | 'dashboard'
  | 'jobs'
  | 'applications'
  | 'events'
  | 'cv'
  | 'inbox'
  | 'profile'
  | 'agents'
  | 'interview';
