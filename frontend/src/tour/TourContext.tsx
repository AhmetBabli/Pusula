import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { TOUR_STEPS, TOUR_STORAGE_KEY, TourStep } from './tourSteps';
import type { Tab } from '../types/tab';

interface TourContextValue {
  active: boolean;
  stepIndex: number;
  step: TourStep | null;
  totalSteps: number;
  isFirst: boolean;
  isLast: boolean;
  start: () => void;
  next: () => void;
  back: () => void;
  skip: () => void;
  finish: () => void;
}

const TourContext = createContext<TourContextValue | null>(null);

export function useTour(): TourContextValue {
  const ctx = useContext(TourContext);
  if (!ctx) throw new Error('useTour, bir <TourProvider> içinde kullanılmalı');
  return ctx;
}

interface TourProviderProps {
  activeTab: Tab;
  onNavigate: (tab: Tab) => void;
  // İlk defa gelen (turu daha önce bitirmemiş/geçmemiş) kullanıcılarda otomatik başlat.
  autoStartIfNew?: boolean;
  children: React.ReactNode;
}

export function TourProvider({ activeTab, onNavigate, autoStartIfNew = false, children }: TourProviderProps) {
  const [active, setActive] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const step = active ? TOUR_STEPS[stepIndex] : null;

  // Adım değişince, o adımın ait olduğu sekmede değilsek otomatik geçiş yap —
  // kullanıcı elle sekme değiştirmek zorunda kalmadan turu takip edebilsin.
  useEffect(() => {
    if (step && step.tab !== activeTab) {
      onNavigate(step.tab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepIndex, active]);

  const start = useCallback(() => {
    setStepIndex(0);
    setActive(true);
  }, []);

  const endTour = useCallback(() => {
    setActive(false);
    try {
      localStorage.setItem(TOUR_STORAGE_KEY, '1');
    } catch {
      // localStorage kullanılamıyorsa (gizli sekme vb.) sessizce yut — tur yine de çalışır,
      // sadece bir sonraki ziyarette hatırlanmaz.
    }
  }, []);

  const next = useCallback(() => {
    setStepIndex((i) => {
      if (i >= TOUR_STEPS.length - 1) {
        endTour();
        return i;
      }
      return i + 1;
    });
  }, [endTour]);

  const back = useCallback(() => {
    setStepIndex((i) => Math.max(0, i - 1));
  }, []);

  const skip = useCallback(() => endTour(), [endTour]);
  const finish = useCallback(() => endTour(), [endTour]);

  useEffect(() => {
    if (!autoStartIfNew) return;
    let alreadyDone = false;
    try {
      alreadyDone = localStorage.getItem(TOUR_STORAGE_KEY) === '1';
    } catch {
      alreadyDone = false;
    }
    if (!alreadyDone) {
      // Panel ilk render'ını (nav öğelerinin DOM'a gelmesini) bekle. Not: burada
      // "sadece bir kez çalış" ref-koruması KASITLI OLARAK yok — StrictMode'un
      // geliştirmede efektleri mount→cleanup→mount olarak iki kez çalıştırması,
      // böyle bir korumayla zamanlayıcının hiç ateşlenmeden iptal edilmesine yol
      // açıyordu. Bağımlılıklar sabit olduğu için efekt gerçek kullanımda zaten
      // yalnızca bir kez çalışır; StrictMode'daki ikinci çalıştırma kendi
      // zamanlayıcısını kurup öncekinin iptalinin yerini alıyor.
      const t = setTimeout(() => start(), 700);
      return () => clearTimeout(t);
    }
  }, [autoStartIfNew, start]);

  const value: TourContextValue = {
    active,
    stepIndex,
    step,
    totalSteps: TOUR_STEPS.length,
    isFirst: stepIndex === 0,
    isLast: stepIndex === TOUR_STEPS.length - 1,
    start,
    next,
    back,
    skip,
    finish,
  };

  return <TourContext.Provider value={value}>{children}</TourContext.Provider>;
}
