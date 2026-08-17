import { useState, useEffect, useRef } from 'react';
import { getToken } from '../services/api';
import { translateStatic } from '../i18n/LanguageContext';

export type TaskStatus = 'idle' | 'pending' | 'running' | 'done' | 'failed' | 'not_found';

export interface TaskState {
  task_id: string | null;
  status: TaskStatus;
  progress: number;
  result: unknown;
  error: string | null;
  updated_at: string | null;
}

const INITIAL_STATE: TaskState = {
  task_id: null,
  status: 'idle',
  progress: 0,
  result: null,
  error: null,
  updated_at: null,
};

/**
 * Arka plan görevini SSE üzerinden takip eden hook.
 *
 * @example
 * const { task, startTracking, reset } = useTaskStream();
 *
 * const handleSync = async () => {
 *   const { task_id } = await syncJobs();
 *   startTracking(task_id);
 * };
 */
export function useTaskStream() {
  const [task, setTask] = useState<TaskState>(INITIAL_STATE);
  const esRef = useRef<EventSource | null>(null);

  const close = () => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  };

  const reset = () => {
    close();
    setTask(INITIAL_STATE);
  };

  const startTracking = (taskId: string) => {
    // Önceki akışı kapat
    close();

    setTask((prev) => ({ ...prev, task_id: taskId, status: 'pending', progress: 0 }));

    // Not: Native EventSource API custom header taşıyamaz, bu yüzden token query parametresi olarak gider.
    const token = getToken() || '';
    const es = new EventSource(`/api/tasks/${taskId}/stream?token=${encodeURIComponent(token)}`);
    esRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskState;
        setTask(data);

        // Görev bitti veya başarısız — bağlantıyı kapat
        if (data.status === 'done' || data.status === 'failed' || data.status === 'not_found') {
          close();
        }
      } catch {
        // JSON parse hatası — sessizce geç
      }
    };

    es.onerror = () => {
      setTask((prev) => ({
        ...prev,
        status: 'failed',
        error: translateStatic('common_sse_disconnected'),
      }));
      close();
    };
  };

  // Component unmount olunca EventSource'u temizle
  useEffect(() => {
    return () => close();
  }, []);

  return { task, startTracking, reset };
}
