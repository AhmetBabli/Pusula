import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Send, ChevronRight, RotateCcw, Loader2, Mail, CheckCircle2, AlertTriangle, Target, Search } from 'lucide-react';
import { useLanguage, translateStatic } from '../../i18n/LanguageContext';
import { getToken } from '../../services/api';

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

export function InterviewCoach({ companyName = '', jobTitle = '', jobDescription = '', jobId }: InterviewCoachProps) {
  const { t } = useLanguage();
  const [company, setCompany] = useState(companyName);
  const [title, setTitle] = useState(jobTitle);
  const [roundType, setRoundType] = useState<'technical' | 'hr' | 'mixed'>('mixed');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [history, setHistory] = useState<{ question: Question; evaluation: Evaluation }[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [loadingEval, setLoadingEval] = useState(false);
  const [phase, setPhase] = useState<'setup' | 'interview' | 'results'>('setup');
  const [error, setError] = useState<string | null>(null);

  // Outreach Integration State
  const [outreachResult, setOutreachResult] = useState<{cold_email: string, linkedin_dm: string} | null>(null);
  const [loadingOutreach, setLoadingOutreach] = useState(false);

  const sessionId = crypto.randomUUID();

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

  const startInterview = async () => {
    setLoadingQuestions(true);
    setError(null);
    try {
      const data = await apiPost('/interview/start', {
        session_id: sessionId,
        company_name: company,
        job_title: title,
        job_description: jobDescription,
        job_id: jobId,
        round_type: roundType,
        question_count: 5,
      });
      setQuestions(data.questions || []);
      setCurrentIdx(0);
      setHistory([]);
      setEvaluation(null);
      setAnswer('');
      setPhase('interview');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim() || !questions[currentIdx]) return;
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
        answer,
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

  const nextQuestion = () => {
    if (currentIdx + 1 >= questions.length) {
      setPhase('results');
    } else {
      setCurrentIdx(i => i + 1);
      setAnswer('');
      setEvaluation(null);
    }
  };

  const avgScore = history.length > 0
    ? Math.round(history.reduce((s, h) => s + h.evaluation.score, 0) / history.length)
    : 0;

  const scoreColor = (s: number) =>
    s >= 75 ? 'text-emerald-500' : s >= 50 ? 'text-primary' : 'text-error';

  // ── Setup Phase ──────────────────────────────────────────────────────────
  if (phase === 'setup') {
    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto space-y-6">
        <div className="flex flex-col items-center text-center space-y-2 mb-8">
          <div className="w-16 h-16 rounded-md bg-primary-container/15 flex items-center justify-center mb-2">
            <Target className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-2xl font-headline font-semibold text-on-surface">{t('interview_setup_title')}</h2>
          <p className="text-on-surface-variant font-body">{t('interview_setup_subtitle')}</p>
        </div>

        <div className="bg-surface-container border border-outline-variant/10 rounded-lg p-6 md:p-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-label font-medium text-on-surface-variant mb-2">{t('interview_target_company')}</label>
              <input
                className="w-full bg-surface-container-highest border border-outline-variant/10 rounded-md px-4 py-3 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors"
                placeholder={t('interview_target_company_placeholder')}
                value={company}
                onChange={e => setCompany(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-xs font-label font-medium text-on-surface-variant mb-2">{t('interview_target_position')}</label>
              <input
                className="w-full bg-surface-container-highest border border-outline-variant/10 rounded-md px-4 py-3 text-sm font-body text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-colors"
                placeholder={t('interview_target_position_placeholder')}
                value={title}
                onChange={e => setTitle(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-xs font-label font-medium text-on-surface-variant mb-2">{t('interview_type_label')}</label>
              <div className="flex gap-3">
                {(['technical', 'hr', 'mixed'] as const).map(rt => (
                  <button
                    key={rt}
                    onClick={() => setRoundType(rt)}
                    className={`flex-1 py-3 text-sm font-label rounded-md border transition-all duration-150 active:scale-[0.98] ${
                      roundType === rt
                        ? 'text-primary border-primary-container/50 bg-primary-container/10'
                        : 'text-on-surface-variant border-outline-variant/10 hover:border-outline-variant/20 hover:bg-surface-container-highest'
                    }`}
                  >
                    {rt === 'technical' ? t('interview_type_technical') : rt === 'hr' ? t('interview_type_hr') : t('interview_type_mixed')}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm" role="alert">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={startInterview}
            disabled={!company.trim() || loadingQuestions}
            className="w-full py-3.5 mt-4 text-sm font-label text-white bg-primary-container rounded-md hover:bg-blue-700 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150 flex items-center justify-center gap-2"
          >
            {loadingQuestions ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('interview_preparing')}</> : t('interview_start')}
          </button>
        </div>
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
                {loadingOutreach ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('interview_outreach_generating')}</> : t('interview_outreach_generate_draft')}
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
            onClick={() => { setPhase('setup'); setHistory([]); setQuestions([]); setOutreachResult(null); }}
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
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-3xl mx-auto space-y-6" id="interview">
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
      <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-emerald-500 rounded-full"
          initial={{ width: `${((currentIdx) / questions.length) * 100}%` }}
          animate={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
        />
      </div>

      {/* Question */}
      <div className="bg-surface-container border border-outline-variant/10 rounded-lg p-6 md:p-8 mt-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 h-full bg-primary-container"></div>
        <div className="flex gap-4">
          <MessageSquare className="w-6 h-6 text-primary shrink-0 mt-1" />
          <p className="text-lg md:text-xl font-headline text-on-surface leading-relaxed font-medium">{q?.question}</p>
        </div>
      </div>

      {/* Answer Area */}
      <AnimatePresence mode="wait">
        {!evaluation ? (
          <motion.div key="answer" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-4 pt-4">
            <textarea
              className="w-full bg-surface-container border border-outline-variant/10 rounded-lg p-5 text-base font-body text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container resize-none transition-all duration-150"
              rows={6}
              placeholder={t('interview_answer_placeholder')}
              value={answer}
              onChange={e => setAnswer(e.target.value)}
            />
            {error && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-error/10 border border-error/20 text-error text-sm" role="alert">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            <div className="flex justify-end">
              <button
                onClick={submitAnswer}
                disabled={!answer.trim() || loadingEval}
                className="flex items-center gap-2 px-6 py-3 text-sm font-label text-white bg-primary-container border border-transparent rounded-md hover:bg-blue-700 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 transition-all duration-150"
              >
                {loadingEval ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('interview_analyzing')}</> : <><Send className="w-4 h-4" /> {t('interview_submit_answer')}</>}
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
