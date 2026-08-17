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

export type AgentName = 'web_search' | 'cv_architect' | 'interview_coach' | 'outreach' | 'system';

export interface AgentStates {
  web_search: AgentEvent;
  cv_architect: AgentEvent;
  interview_coach: AgentEvent;
  outreach: AgentEvent;
}

const makeIdle = (agent: string): AgentEvent => ({
  agent, status: 'idle', step: '', progress: 0, data: {},
});

const INITIAL: AgentStates = {
  web_search: makeIdle('web_search'),
  cv_architect: makeIdle('cv_architect'),
  interview_coach: makeIdle('interview_coach'),
  outreach: makeIdle('outreach'),
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
  const sessionId = useRef<string>(crypto.randomUUID());

  const addLog = useCallback((msg: string) => {
    setLogs((prev) => [...prev.slice(-99), `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const token = getToken() || '';
    const ws = new WebSocket(`ws://localhost:8000/ws/agents/${sessionId.current}?token=${encodeURIComponent(token)}`);
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
      addLog(`🔌 ${translateStatic('ws_reconnecting')}`);
      setTimeout(connect, 3000); // Auto-reconnect
    };

    ws.onerror = () => {
      addLog(`❌ ${translateStatic('ws_error')}`);
    };
  }, [addLog]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
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
