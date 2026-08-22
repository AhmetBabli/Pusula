import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Send, ChevronRight, RotateCcw, Mail, CheckCircle2, AlertTriangle, Info, Compass, Volume2, Mic, Square, X, Keyboard } from 'lucide-react';
import { useLanguage, translateStatic } from '../../i18n/LanguageContext';
import { getToken } from '../../services/api';
import { InterviewMascotScene } from './InterviewMascotScene';

interface Question {
  id: number;
  question: string;
  type: 'technical' | 'hr';
  hint: string;
}

interface Evaluation {
  score: number;
  feedback: string;
  strengths: string[];
  improvements: string[];
  model_answer_hint: string;
}

interface InterviewCoachProps {
  companyName?: string;
  jobTitle?: string;
  jobDescription?: string;
  jobId?: number;
  onExitRoom?: () => void;
}

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

export function InterviewCoach({ companyName = '', jobTitle = '', jobDescription = '', jobId, onExitRoom }: InterviewCoachProps) {
  const { t } = useLanguage();
  const [company, setCompany] = useState(companyName);
  const [title, setTitle] = useState(jobTitle);
  const roundType: 'technical' | 'hr' | 'mixed' = 'mixed';
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [history, setHistory] = useState<{ question: Question; evaluation: Evaluation }[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [loadingEval, setLoadingEval] = useState(false);
  const [phase, setPhase] = useState<'setup' | 'interview' | 'results'>('setup');
  const [error, setError] = useState<string | null>(null);
  const [personalized, setPersonalized] = useState(true);

  // Maskotla sohbet şeklinde kurulum: önce şirket, sonra bölüm/pozisyon sorulur.
  // İkisi de dışarıdan (props) zaten geldiyse ilgili adım(lar) atlanır.
  const [setupStep, setSetupStep] = useState<'ask_company' | 'ask_department' | 'researching'>(
    companyName ? (jobTitle ? 'researching' : 'ask_department') : 'ask_company'
  );
  const [chatInput, setChatInput] = useState('');
  const [researchingIdx, setResearchingIdx] = useState(0);
  const RESEARCHING_KEYS = ['interview_researching_1', 'interview_researching_2', 'interview_researching_3'] as const;

  // Outreach Integration State
  const [outreachResult, setOutreachResult] = useState<{cold_email: string, linkedin_dm: string} | null>(null);
  const [loadingOutreach, setLoadingOutreach] = useState(false);

  // Sesli sohbet: soru otomatik seslendirilir (TTS), bitince mikrofon otomatik
  // açılır (STT), kullanıcı sessize düşünce cevap otomatik gönderilir — tıklama
  // gerekmeden gerçek bir görüşme akışı. Butonlar manuel müdahale için hep orada.
  const [speaking, setSpeaking] = useState(false);
  const [listening, setListening] = useState(false);
  const [sttSupported, setSttSupported] = useState(true);
  const [micErrorCode, setMicErrorCode] = useState<string | null>(null);
  const [textInputMode, setTextInputMode] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const autoSubmitPendingRef = useRef(false);
  const submitAnswerRef = useRef<(answerOverride?: string) => void>(() => {});

  // useRef ile: component gövdesinde crypto.randomUUID() çağırmak her
  // render'da (her interim transkript güncellemesinde bile) yeni bir ID
  // üretiyordu — araştırma/soru/değerlendirme istekleri hep farklı
  // session_id taşıyordu, sunucu tarafında hiçbir oturum korelasyonu
  // kurulamıyordu.
  const sessionId = useRef(crypto.randomUUID()).current;

  const clearSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  };

  // Kullanıcı konuşmayı bıraktıktan ~2sn sonra dinlemeyi durdurup cevabı otomatik gönder
  const resetSilenceTimer = () => {
    if (!autoSubmitPendingRef.current) return;
    clearSilenceTimer();
    silenceTimerRef.current = setTimeout(() => {
      try { recognitionRef.current?.stop(); } catch {}
    }, 2200);
  };

  const startListeningAuto = () => {
    if (!recognitionRef.current || !sttSupported) return;
    autoSubmitPendingRef.current = true;
    setMicErrorCode(null);
    try {
      recognitionRef.current.start();
      setListening(true);
    } catch (e: any) {
      // Sadece "zaten çalışıyor" (InvalidStateError) sessizce yok sayılır —
      // başka bir hata (ör. tarayıcının konuşma tanıma motoru gerçekte
      // çalışmıyorsa) daha önce burada tamamen yutuluyordu, kullanıcı hiçbir
      // şey görmüyordu. Artık gerçek nedeni gösteriyoruz.
      autoSubmitPendingRef.current = false;
      if (e?.name !== 'InvalidStateError') {
        setMicErrorCode(e?.name || 'start-failed');
      }
    }
  };

  // Tarayıcının kendi ücretsiz Speech Synthesis motorunu kullanır — Google
  // Cloud TTS anahtarı gerekmez (kullanıcı paralı kısmı şimdilik istemedi).
  const speakQuestion = (text: string): Promise<void> => {
    if (!text) return Promise.resolve();
    const synth = (window as any).speechSynthesis;
    if (!synth) return Promise.resolve(); // tarayıcı desteklemiyorsa sessizce geç, STT ile sohbet devam eder
    return new Promise<void>((resolve) => {
      try {
        synth.cancel(); // önceki konuşma varsa kes
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'tr-TR';
        const trVoice = synth.getVoices().find((v: any) => v.lang?.toLowerCase().startsWith('tr'));
        if (trVoice) utterance.voice = trVoice;
        utterance.onstart = () => setSpeaking(true);
        utterance.onend = () => { setSpeaking(false); resolve(); };
        utterance.onerror = () => { setSpeaking(false); resolve(); };
        synth.speak(utterance);
      } catch {
        setSpeaking(false);
        resolve();
      }
    });
  };

  // Konuşma tanıma (STT) motorunu bir kere kur — soru değiştikçe yeniden kurmaya gerek yok
  useEffect(() => {
    const SpeechRecognitionCtor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setSttSupported(false);
      setTextInputMode(true); // mikrofon hiç yoksa direkt yazma moduna düş
      return;
    }
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = 'tr-TR';
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const chunk = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalTranscript += chunk;
        else interim += chunk;
      }
      if (finalTranscript.trim()) {
        setAnswer(prev => (prev ? `${prev} ${finalTranscript.trim()}` : finalTranscript.trim()));
        setInterimTranscript('');
      } else {
        // Chrome çoğu zaman sonucu hiç "final" işaretlemeden bırakıyor — bu
        // yüzden geçici (interim) metni de göstermezsek kullanıcı konuşsa
        // bile ekranda hiçbir şey görünmüyordu.
        setInterimTranscript(interim);
      }
      resetSilenceTimer(); // konuşma devam ettikçe "sustu" sayacını sıfırla
    };
    recognition.onerror = (e: any) => {
      setListening(false);
      clearSilenceTimer();
      // 'aborted' kendi stop() çağrılarımızdan gelir — gerçek bir hata değil, gösterme
      if (e?.error && e.error !== 'aborted') {
        setMicErrorCode(e.error);
        autoSubmitPendingRef.current = false;
      }
    };
    recognition.onend = () => {
      setListening(false);
      clearSilenceTimer();
      const shouldAutoSubmit = autoSubmitPendingRef.current;
      autoSubmitPendingRef.current = false;
      // Kalan interim metni kaybetmeyelim — kesinleşmemiş olsa da cevabın
      // parçası. Otomatik gönderim varsa, tam metni (answer state'inin henüz
      // güncellenmemiş olabileceği bu tick içinde) doğrudan hesaplayıp
      // submitAnswer'a parametre olarak veriyoruz — state okuması stale kalabilir.
      setInterimTranscript(prevInterim => {
        const leftover = prevInterim.trim();
        if (!leftover) {
          if (shouldAutoSubmit) submitAnswerRef.current();
          return '';
        }
        setAnswer(prevAnswer => {
          const merged = prevAnswer ? `${prevAnswer} ${leftover}` : leftover;
          if (shouldAutoSubmit) submitAnswerRef.current(merged);
          return merged;
        });
        return '';
      });
    };
    recognitionRef.current = recognition;

    return () => {
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      try { recognition.stop(); } catch {}
    };
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) return;
    autoSubmitPendingRef.current = false; // manuel kontrol: gönderme kararı kullanıcıda kalsın
    clearSilenceTimer();
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      setMicErrorCode(null);
      try {
        recognitionRef.current.start();
        setListening(true);
      } catch (e: any) {
        if (e?.name !== 'InvalidStateError') {
          setMicErrorCode(e?.name || 'start-failed');
        }
      }
    }
  };

  // Yeni soru geldiğinde: sesli sor, bitince otomatik dinlemeye geç (sesli sohbet akışı)
  useEffect(() => {
    if (phase === 'interview' && questions[currentIdx]) {
      speakQuestion(questions[currentIdx].question).then(startListeningAuto);
    }
    return () => {
      audioRef.current?.pause();
      clearSilenceTimer();
      autoSubmitPendingRef.current = false;
      try { recognitionRef.current?.stop(); } catch {}
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, currentIdx]);

  // Değerlendirme geldiğinde skoru ve geri bildirimi de sesli oku
  useEffect(() => {
    if (evaluation) {
      speakQuestion(`${evaluation.score}. ${evaluation.feedback}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evaluation]);

  // Maskot, kurulum sohbetinin her adımında ilgili soruyu sesli sorar
  useEffect(() => {
    if (phase !== 'setup') return;
    if (setupStep === 'ask_company') speakQuestion(t('interview_mascot_greeting'));
    else if (setupStep === 'ask_department') speakQuestion(t('interview_mascot_ask_department'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, setupStep]);

  // Şirket + pozisyon dışarıdan (props) zaten geldiyse sohbeti atlayıp direkt araştırmaya başla
  useEffect(() => {
    if (setupStep === 'researching') startInterview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Araştırma sırasında maskotun söylediği satırı birkaç saniyede bir değiştir
  useEffect(() => {
    if (!(phase === 'setup' && setupStep === 'researching' && loadingQuestions)) return;
    setResearchingIdx(0);
    const id = setInterval(() => {
      setResearchingIdx(i => (i + 1) % RESEARCHING_KEYS.length);
    }, 2400);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, setupStep, loadingQuestions]);

  const generateOutreach = async () => {
    setLoadingOutreach(true);
    setError(null);
    try {
      const data = await apiPost('/outreach/sync', {
        session_id: sessionId,
        company_name: company || t('outreach_fallback_company'),
        job_title: title || t('outreach_fallback_position'),
        job_description: jobDescription
      });
      setOutreachResult(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingOutreach(false);
    }
  };

  const startInterview = async (titleOverride?: string) => {
    setLoadingQuestions(true);
    setError(null);
    try {
      const data = await apiPost('/interview/start', {
        session_id: sessionId,
        company_name: company,
        job_title: titleOverride ?? title,
        job_description: jobDescription,
        job_id: jobId,
        round_type: roundType,
      });
      setQuestions(data.questions || []);
      setPersonalized(data.personalized !== false);
      setCurrentIdx(0);
      setHistory([]);
      setEvaluation(null);
      setAnswer('');
      setInterimTranscript('');
      setPhase('interview');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const submitCompanyStep = () => {
    if (!chatInput.trim()) return;
    setCompany(chatInput.trim());
    setChatInput('');
    setSetupStep('ask_department');
  };

  const submitDepartmentStep = () => {
    if (!chatInput.trim()) return;
    const finalTitle = chatInput.trim();
    setTitle(finalTitle);
    setChatInput('');
    setSetupStep('researching');
    startInterview(finalTitle);
  };

  const retryStart = () => {
    startInterview();
  };

  const submitAnswer = async (answerOverride?: string) => {
    // Sessizlik sayacı otomatik gönderirken, o an henüz commit edilmemiş
    // interim metni de içeren tam cevabı doğrudan parametre olarak verir —
    // answer state'ini okumak bu durumda bir tık geriden (stale) kalabilirdi.
    const finalAnswer = (answerOverride ?? answer).trim();
    if (!finalAnswer || !questions[currentIdx]) return;
    autoSubmitPendingRef.current = false;
    clearSilenceTimer();
    try { recognitionRef.current?.stop(); } catch {}
    setLoadingEval(true);
    setError(null);
    const q = questions[currentIdx];
    try {
      const data = await apiPost('/interview/answer', {
        session_id: sessionId,
        question_id: q.id,
        question: q.question,
        question_type: q.type,
        hint: q.hint,
        answer: finalAnswer,
        company_name: company,
        job_title: title,
      });
      const ev: Evaluation = data.evaluation;
      setEvaluation(ev);
      setHistory(prev => [...prev, { question: q, evaluation: ev }]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingEval(false);
    }
  };

  // Sessizlik sayacı submitAnswer'ı çağırdığında her zaman en güncel halini kullansın
  useEffect(() => {
    submitAnswerRef.current = submitAnswer;
  });

  const nextQuestion = () => {
    if (currentIdx + 1 >= questions.length) {
      setPhase('results');
    } else {
      setCurrentIdx(i => i + 1);
      setAnswer('');
      setInterimTranscript('');
      setEvaluation(null);
    }
  };

  const avgScore = history.length > 0
    ? Math.round(history.reduce((s, h) => s + h.evaluation.score, 0) / history.length)
    : 0;

  const scoreColor = (s: number) =>
    s >= 75 ? 'text-emerald-500' : s >= 50 ? 'text-primary' : 'text-error';

  // Web Speech API'nin ham hata kodunu (bkz. MDN SpeechRecognitionErrorEvent)
  // anlaşılır bir Türkçe ipucuna çevirir; ham kodu da yanında gösteriyoruz ki
  // tanımadığımız bir kod gelirse bile kullanıcı/biz teşhis edebilelim.
  const micErrorHint = (code: string) => {
    switch (code) {
      case 'not-allowed':
      case 'service-not-allowed':
        return t('interview_mic_error_not_allowed');
      case 'audio-capture':
        return t('interview_mic_error_no_device');
      case 'network':
        return t('interview_mic_error_network');
      case 'no-speech':
        return t('interview_mic_error_no_speech');
      case 'start-failed':
        return t('interview_mic_error_start_failed');
      default:
        return t('interview_mic_error_unknown');
    }
  };

  // Maskot masanın uzak ucunda oturuyor — kollar masaya uzanıyor, gövdenin geri
  // kalanı masa yüzeyinin arkasında kalıyor. Kullanıcı için ayrı bir avatar
  // çizilmiyor: masanın yakın (geniş) ucu izleyicinin kendisini temsil ediyor.
  // Mülakat "odası": sidebar/başlık kayboluyor, sahne tüm ekranı kaplıyor —
  // gerçekten bir odaya girmiş gibi. Çıkmak için sağ üstte bir X butonu var.
  const renderRoomShell = (content: React.ReactNode) => (
    <div className="fixed inset-0 z-50 bg-surface overflow-y-auto">
      <button
        type="button"
        onClick={() => onExitRoom?.()}
        className="fixed top-4 right-4 z-10 w-10 h-10 rounded-full bg-surface-container border border-outline-variant/10 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest transition-colors duration-150"
        title={t('interview_exit_room')}
        aria-label={t('interview_exit_room')}
      >
        <X className="w-5 h-5" />
      </button>
      <div className="min-h-full flex items-center justify-center p-6 md:p-10">
        {content}
      </div>
    </div>
  );

  const renderMascotStage = (maxWidth: number) => (
    <div className="mx-auto" style={{ maxWidth }}>
      <InterviewMascotScene
        speaking={speaking}
        listening={listening}
        thinking={phase === 'setup' && setupStep === 'researching' && loadingQuestions}
      />
    </div>
  );

  // ── Setup Phase (maskotla sohbet) ───────────────────────────────────────
  if (phase === 'setup') {
    const isResearching = setupStep === 'researching';
    const mascotLine =
      setupStep === 'ask_company' ? t('interview_mascot_greeting') :
      setupStep === 'ask_department' ? t('interview_mascot_ask_department') :
      t(RESEARCHING_KEYS[researchingIdx]);
    const submitChatStep = () => (setupStep === 'ask_company' ? submitCompanyStep() : submitDepartmentStep());

    return renderRoomShell(
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl w-full mx-auto space-y-6">
        {/* Pusula masanın uzak ucunda oturuyor, sen (izleyici) yakın uçtasın */}
        {renderMascotStage(440)}

        {/* Maskotun söylediği satır */}
        <div className="bg-surface-container border border-outline-variant/10 rounded-lg p-6 md:p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary-container"></div>
          <div className="flex items-start gap-3">
            <MessageSquare className="w-5 h-5 text-primary shrink-0 mt-1" />
            <p className="text-base md:text-lg font-headline text-on-surface leading-relaxed font-medium">
              {mascotLine}
            </p>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm" role="alert">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {isResearching ? (
          error && (
            <div className="flex justify-end">
              <button
                onClick={retryStart}
                className="flex items-center gap-2 px-6 py-3 text-sm font-label text-on-surface bg-surface-container-highest border border-outline-variant/10 rounded-md hover:bg-outline-variant/10 active:scale-[0.98] transition-all duration-150"
              >
                <RotateCcw className="w-4 h-4" /> {t('interview_retry')}
              </button>
            </div>
          )
        ) : (
          <div className="bg-surface-container border border-outline-variant/10 rounded-lg p-4 md:p-6">
            <div className="flex gap-2">
              <input
                className="flex-1 bg-surface-container-highest border border-outline-variant/10 rounded-md px-4 py-3 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors"
                placeholder={setupStep === 'ask_company' ? t('interview_target_company_placeholder') : t('interview_target_position_placeholder')}
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') submitChatStep(); }}
                autoFocus
              />
              <button
                onClick={submitChatStep}
                disabled={!chatInput.trim()}
                className="px-5 py-3 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150 flex items-center gap-2 shrink-0"
                aria-label={t('interview_start')}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </motion.div>
    );
  }

  // ── Results Phase ────────────────────────────────────────────────────────
  if (phase === 'results') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-3xl mx-auto space-y-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-headline font-semibold text-on-surface mb-2">{t('interview_results_title')}</h2>
          <p className="text-on-surface-variant font-body">{t('interview_results_subtitle')}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="md:col-span-1 bg-surface-container border border-outline-variant/10 rounded-lg p-6 text-center flex flex-col justify-center">
            <div className={`text-6xl tabular-nums font-bold mb-2 ${scoreColor(avgScore)}`}>{avgScore}</div>
            <div className="text-xs font-label font-medium text-on-surface-variant">{t('interview_average_score')}</div>
          </div>

          <div className="md:col-span-2 bg-surface-container border border-outline-variant/10 rounded-lg p-6 flex flex-col justify-center">
            <h3 className="text-sm font-label font-semibold text-on-surface mb-4">{t('interview_summary_verdict')}</h3>
            <p className="text-sm font-body text-on-surface-variant leading-relaxed">
              {avgScore >= 80 ? t('interview_verdict_strong') :
               avgScore >= 60 ? t('interview_verdict_moderate') :
               t('interview_verdict_needs_work')}
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-label font-semibold text-on-surface mb-2">{t('interview_question_breakdown')}</h3>
          {history.map((h, i) => (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }} key={i} className="bg-surface-container border border-outline-variant/10 rounded-lg p-5 space-y-3 hover:border-outline-variant/20 transition-colors duration-150">
              <div className="flex justify-between items-start gap-6">
                <div className="text-base font-headline font-medium text-on-surface">{h.question.question}</div>
                <span className={`text-xl tabular-nums font-bold shrink-0 ${scoreColor(h.evaluation.score)}`}>{h.evaluation.score}</span>
              </div>
              <div className="text-sm font-body text-on-surface-variant bg-surface-container-highest p-4 rounded-lg">{h.evaluation.feedback}</div>
            </motion.div>
          ))}
        </div>

        {/* OUTREACH INTEGRATION */}
        <div className="mt-12 pt-8 border-t border-outline-variant/10 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="text-lg font-headline font-semibold text-on-surface flex items-center gap-2 mb-1">
                <Send className="w-5 h-5 text-primary" />
                {t('interview_outreach_title')}
              </div>
              <div className="text-sm font-body text-on-surface-variant">{t('interview_outreach_desc')}</div>
            </div>
            {!outreachResult && (
              <button
                onClick={generateOutreach}
                disabled={loadingOutreach}
                className="px-5 py-2.5 text-sm font-label bg-primary-container text-white rounded-md hover:bg-blue-700 active:scale-[0.97] transition-all duration-150 flex items-center gap-2 disabled:opacity-50 disabled:active:scale-100 shrink-0"
              >
                {loadingOutreach ? <><Compass className="w-4 h-4 animate-spin" /> {t('interview_outreach_generating')}</> : t('interview_outreach_generate_draft')}
              </button>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm" role="alert">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {outreachResult && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surface-container border border-outline-variant/10 rounded-md p-5">
                <div className="text-xs font-label font-semibold text-primary mb-3 flex items-center gap-1.5"><Mail className="w-3.5 h-3.5"/> {t('interview_outreach_cold_email')}</div>
                <pre className="text-sm font-body text-on-surface-variant whitespace-pre-wrap leading-relaxed">
                  {outreachResult.cold_email}
                </pre>
              </div>
              <div className="bg-surface-container border border-outline-variant/10 rounded-md p-5">
                <div className="text-xs font-label font-semibold text-primary mb-3 flex items-center gap-1.5"><MessageSquare className="w-3.5 h-3.5"/> {t('interview_outreach_linkedin_dm')}</div>
                <pre className="text-sm font-body text-on-surface-variant whitespace-pre-wrap leading-relaxed">
                  {outreachResult.linkedin_dm}
                </pre>
              </div>
            </motion.div>
          )}
        </div>

        <div className="flex justify-end pt-8">
          <button
            onClick={() => { setPhase('setup'); setSetupStep('ask_company'); setChatInput(''); setHistory([]); setQuestions([]); setOutreachResult(null); if (sttSupported) setTextInputMode(false); }}
            className="flex items-center gap-2 px-6 py-3 text-sm font-label text-on-surface bg-surface-container-highest border border-outline-variant/10 rounded-md hover:bg-outline-variant/10 active:scale-[0.98] transition-all duration-150"
          >
            <RotateCcw className="w-4 h-4" /> {t('interview_new_simulation')}
          </button>
        </div>
      </motion.div>
    );
  }

  // ── Interview Phase ──────────────────────────────────────────────────────
  const q = questions[currentIdx];
  return renderRoomShell(
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-3xl w-full mx-auto space-y-6" id="interview">
      {/* Progress */}
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs font-label font-medium text-on-surface-variant">
          {t('interview_question_progress')} {currentIdx + 1} / {questions.length}
        </div>
        <span className={`text-xs font-label px-3 py-1 rounded-md border ${
          q.type === 'technical'
            ? 'text-primary border-primary-container/30 bg-primary-container/10'
            : 'text-secondary border-secondary/30 bg-secondary/10'
        }`}>
          {q.type === 'technical' ? t('interview_technical_badge') : t('interview_cultural_badge')}
        </span>
      </div>

      {!personalized && (
        <div className="flex items-start gap-2 text-xs font-body text-on-surface-variant bg-surface-container-lowest border border-outline-variant/10 rounded-md px-3 py-2.5 mb-2">
          <Info className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
          <span>{t('interview_fallback_notice')}</span>
        </div>
      )}

      <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-emerald-500 rounded-full"
          initial={{ width: `${((currentIdx) / questions.length) * 100}%` }}
          animate={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
        />
      </div>

      {/* Pusula masanın uzak ucunda oturuyor, sen (izleyici) yakın uçtasın */}
      <div className="mt-4">{renderMascotStage(340)}</div>

      {(speaking || listening) && (
        <div className={`flex items-center justify-center gap-2 text-xs font-label ${speaking ? 'text-primary' : 'text-error'}`}>
          <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${speaking ? 'bg-primary' : 'bg-error'}`} />
          {speaking ? t('interview_ai_speaking') : t('interview_ai_listening')}
        </div>
      )}

      {/* Question */}
      <div className="bg-surface-container border border-outline-variant/10 rounded-lg p-6 md:p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 h-full bg-primary-container"></div>
        <div className="flex gap-4">
          <MessageSquare className="w-6 h-6 text-primary shrink-0 mt-1" />
          <p className="text-lg md:text-xl font-headline text-on-surface leading-relaxed font-medium flex-1">{q?.question}</p>
          <button
            type="button"
            onClick={() => q && speakQuestion(q.question)}
            className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center border transition-all duration-150 ${
              speaking
                ? 'bg-primary-container/15 border-primary-container/40 text-primary animate-pulse'
                : 'bg-surface-container-highest border-outline-variant/10 text-on-surface-variant hover:text-primary hover:border-primary-container/30'
            }`}
            title={t('interview_listen_question')}
            aria-label={t('interview_listen_question')}
          >
            <Volume2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Answer Area */}
      <AnimatePresence mode="wait">
        {!evaluation ? (
          <motion.div key="answer" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-4 pt-4">
            {!textInputMode ? (
              <>
                {/* Konuşma balonu: form kutusu değil, gerçek bir söyleşi gibi */}
                <div className="flex justify-end">
                  <div className={`max-w-[90%] rounded-2xl rounded-tr-sm px-5 py-4 text-base font-body border transition-colors duration-150 ${
                    answer || interimTranscript
                      ? 'bg-primary-container/15 border-primary-container/30 text-on-surface'
                      : 'bg-surface-container border-outline-variant/10 text-on-surface-variant/60 italic'
                  }`}>
                    {answer || interimTranscript ? (
                      <>
                        {answer}
                        {interimTranscript && <span className="opacity-50 italic">{answer ? ' ' : ''}{interimTranscript}</span>}
                      </>
                    ) : t('interview_voice_prompt')}
                  </div>
                </div>

                <div className="flex flex-col items-center gap-3 py-2">
                  <button
                    type="button"
                    onClick={toggleListening}
                    className={`w-16 h-16 rounded-full flex items-center justify-center border-2 transition-all duration-150 active:scale-95 ${
                      listening
                        ? 'bg-error/10 border-error/50 text-error animate-pulse'
                        : 'bg-primary-container/10 border-primary-container/40 text-primary hover:bg-primary-container/20'
                    }`}
                    title={listening ? t('interview_stop_listening') : t('interview_start_listening')}
                    aria-label={listening ? t('interview_stop_listening') : t('interview_start_listening')}
                  >
                    {listening ? <Square className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                  </button>
                  {listening && (
                    <div className="flex items-center gap-2 text-xs font-label text-error">
                      <span className="w-1.5 h-1.5 rounded-full bg-error animate-pulse" />
                      {t('interview_listening_active')}
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => setTextInputMode(true)}
                    className="flex items-center gap-1.5 text-xs font-label text-on-surface-variant hover:text-on-surface underline underline-offset-2"
                  >
                    <Keyboard className="w-3.5 h-3.5" /> {t('interview_switch_to_typing')}
                  </button>
                </div>
              </>
            ) : (
              <div className="space-y-2">
                <div className="relative">
                  <textarea
                    className="w-full bg-surface-container border border-outline-variant/10 rounded-lg p-5 text-base font-body text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container resize-none transition-all duration-150"
                    rows={6}
                    placeholder={t('interview_answer_placeholder')}
                    value={answer}
                    onChange={e => setAnswer(e.target.value)}
                    autoFocus
                  />
                </div>
                {sttSupported && (
                  <button
                    type="button"
                    onClick={() => setTextInputMode(false)}
                    className="flex items-center gap-1.5 text-xs font-label text-on-surface-variant hover:text-on-surface underline underline-offset-2"
                  >
                    <Mic className="w-3.5 h-3.5" /> {t('interview_switch_to_voice')}
                  </button>
                )}
              </div>
            )}
            {micErrorCode && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm" role="alert">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{micErrorHint(micErrorCode)} ({micErrorCode})</span>
              </div>
            )}
            {error && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm" role="alert">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            <div className="flex justify-end">
              <button
                onClick={() => submitAnswer()}
                disabled={!answer.trim() || loadingEval}
                className="flex items-center gap-2 px-6 py-3 text-sm font-label text-white bg-primary-container border border-transparent rounded-md hover:bg-blue-700 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150"
              >
                {loadingEval ? <><Compass className="w-4 h-4 animate-spin" /> {t('interview_analyzing')}</> : <><Send className="w-4 h-4" /> {t('interview_submit_answer')}</>}
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div key="evaluation" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6 pt-4">
            <div className="bg-surface-container border border-outline-variant/10 rounded-lg p-6 md:p-8 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-outline-variant/10">
                <span className="text-sm font-label font-medium text-on-surface-variant">{t('interview_evaluation')}</span>
                <span className={`text-4xl tabular-nums font-bold ${scoreColor(evaluation.score)}`}>{evaluation.score}</span>
              </div>

              <p className="text-base font-body text-on-surface leading-relaxed">{evaluation.feedback}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-md p-4">
                  <div className="text-xs font-label font-semibold text-emerald-500 mb-3 flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5"/> {t('cv_strengths')}</div>
                  <ul className="space-y-2">
                    {evaluation.strengths.map((s, i) => (
                      <li key={i} className="flex gap-2 text-sm font-body text-on-surface-variant"><span className="text-emerald-500 mt-0.5">•</span><span>{s}</span></li>
                    ))}
                  </ul>
                </div>
                <div className="bg-yellow-500/5 border border-yellow-500/10 rounded-md p-4">
                  <div className="text-xs font-label font-semibold text-yellow-500 mb-3 flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5"/> {t('cv_weaknesses')}</div>
                  <ul className="space-y-2">
                    {evaluation.improvements.map((s, i) => (
                      <li key={i} className="flex gap-2 text-sm font-body text-on-surface-variant"><span className="text-yellow-500 mt-0.5">•</span><span>{s}</span></li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={nextQuestion}
                className="flex items-center gap-2 px-6 py-3 text-sm font-label text-on-surface bg-surface-container-highest border border-outline-variant/10 rounded-md hover:bg-outline-variant/10 active:scale-[0.98] transition-all duration-150"
              >
                {currentIdx + 1 >= questions.length ? t('interview_view_results') : t('interview_next_question')}
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

