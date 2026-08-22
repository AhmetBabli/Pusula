import { useState, useEffect, useRef, useCallback } from 'react';
import { getToken } from '../services/api';
import { translateStatic } from '../i18n/LanguageContext';

export interface AgentEvent {
  agent: string;
  status: 'idle' | 'running' | 'done' | 'failed' | 'connected' | 'heartbeat' | 'pong';
  step: string;
  progress: number;
  data: Record<string, unknown>;
  ts?: string;
}

export type AgentName = 'web_search' | 'event_search' | 'cv_architect' | 'interview_coach' | 'outreach' | 'strategy' | 'system';

export interface AgentStates {
  web_search: AgentEvent;
  event_search: AgentEvent;
  cv_architect: AgentEvent;
  interview_coach: AgentEvent;
  outreach: AgentEvent;
  strategy: AgentEvent;
}

const makeIdle = (agent: string): AgentEvent => ({
  agent, status: 'idle', step: '', progress: 0, data: {},
});

const INITIAL: AgentStates = {
  web_search: makeIdle('web_search'),
  event_search: makeIdle('event_search'),
  cv_architect: makeIdle('cv_architect'),
  interview_coach: makeIdle('interview_coach'),
  outreach: makeIdle('outreach'),
  strategy: makeIdle('strategy'),
};

/**
 * Ajan Merkezi WebSocket hook'u.
 * @example
 * const { agents, sessionId, connected, logs, resetAgent } = useAgentWebSocket();
 * // Ajan tetiklemeden önce sessionId'yi backend'e gönderin.
 */
export function useAgentWebSocket() {
  const [agents, setAgents] = useState<AgentStates>(INITIAL);
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  // Eskiden setTimeout(connect, 3000) hiçbir yerde saklanmıyordu — StrictMode'un
  // mount→cleanup→remount döngüsünde her montaj bir soket + bir reconnect
  // zamanlayıcısı sızdırıyordu, sonunda birbirini geçersiz kılan birden fazla
  // soket birikebiliyordu. cancelledRef, unmount edilmiş bir bağlantının
  // yeniden bağlanmaya çalışmasını da engelliyor.
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelledRef = useRef(false);
  const sessionId = useRef<string>(crypto.randomUUID());

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [...prev.slice(-99), `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }, []);

  const clearReconnectTimer = () => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  };

  const connect = useCallback(() => {
    if (cancelledRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const token = getToken() || '';
    // Eskiden ws://localhost:8000 sabit kodluydu — dağıtılan hiçbir ortamda
    // çalışmıyordu (ve HTTPS sayfadan ws:// zaten "mixed content" olarak
    // engellenir). Artık sayfanın kendi origin'inden türetiliyor; Vite dev
    // sunucusunda /ws proxy'si (vite.config.ts) bunu backend'e yönlendiriyor,
    // production'da aynı origin/reverse proxy üzerinden gerçek backend'e gider.
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${proto}//${window.location.host}/ws/agents/${sessionId.current}?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      addLog(`✅ ${translateStatic('ws_connected')}`);
    };

    ws.onmessage = (e) => {
      try {
        const event: AgentEvent = JSON.parse(e.data);
        if (event.agent === 'system') {
          if (event.status === 'heartbeat') ws.send('ping');
          return;
        }
        const agentKey = event.agent as keyof AgentStates;
        if (agentKey in INITIAL) {
          setAgents((prev) => ({ ...prev, [agentKey]: event }));
          if (event.step) addLog(`[${event.agent}] ${event.step}`);
        }
      } catch { /* JSON parse hataları sessizce geçilir */ }
    };

    ws.onclose = () => {
      setConnected(false);
      if (cancelledRef.current) return; // unmount edilmiş bir hook yeniden bağlanmaya çalışmasın
      addLog(`🔌 ${translateStatic('ws_reconnecting')}`);
      clearReconnectTimer();
      reconnectTimerRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      addLog(`❌ ${translateStatic('ws_error')}`);
    };
  }, [addLog]);

  useEffect(() => {
    cancelledRef.current = false;
    connect();
    return () => {
      cancelledRef.current = true;
      clearReconnectTimer();
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);

  const resetAgent = useCallback((agent: keyof AgentStates) => {
    setAgents((prev) => ({ ...prev, [agent]: makeIdle(agent) }));
  }, []);

  return {
    agents,
    sessionId: sessionId.current,
    connected,
    logs,
    resetAgent,
  };
}
