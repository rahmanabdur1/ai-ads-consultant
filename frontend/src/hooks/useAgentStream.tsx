import { useEffect, useRef, useState, useCallback } from 'react';

// ==============================
// TYPES
// ==============================
interface AgentStep {
  type: 'agent_step';
  agent: string;
  status: string;
  message?: string;
}

interface ChatToken {
  type: 'chat_token';
  token: string;
}

interface ChatEnd {
  type: 'chat_end';
}

interface Done {
  type: 'done';
  result: any;
}

interface ErrorMsg {
  type: 'error';
  message: string;
}

type AgentMessage = AgentStep | ChatToken | ChatEnd | Done | ErrorMsg;

interface RunAgentPayload {
  [key: string]: any; // extend with actual keys if known
}

interface ChatPayload {
  message: string;
  [key: string]: any;
}

interface UseAgentStreamReturn {
  connected: boolean;
  agentSteps: AgentStep[];
  chatTokens: string;
  done: any;
  error: string | null;
  runAgent: (payload: RunAgentPayload) => void;
  sendChat: (payload: ChatPayload) => void;
}

// ==============================
// HOOK
// ==============================
export function useAgentStream(sessionId: string): UseAgentStreamReturn {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [chatTokens, setChatTokens] = useState('');
  const [done, setDone] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const host = process.env.NEXT_PUBLIC_WS_HOST || 'localhost:8000';
    const url = `ws://${host}/ws/agent/${sessionId}`;
    ws.current = new WebSocket(url);

    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);

    ws.current.onmessage = (e: MessageEvent<string>) => {
      let data: AgentMessage;
      try {
        data = JSON.parse(e.data);
      } catch (err) {
        console.error('Invalid JSON from agent WS:', e.data);
        return;
      }

      switch (data.type) {
        case 'agent_step':
          setAgentSteps(prev => {
            const index = prev.findIndex(s => s.agent === data.agent);
            if (index >= 0) {
              const updated = [...prev];
              updated[index] = data;
              return updated;
            }
            return [...prev, data];
          });
          break;
        case 'chat_token':
          setChatTokens(prev => prev + data.token);
          break;
        case 'chat_end':
          setChatTokens('');
          break;
        case 'done':
          setDone(data.result);
          break;
        case 'error':
          setError(data.message);
          break;
      }
    };

    return () => ws.current?.close();
  }, [sessionId]);

  const runAgent = useCallback((payload: RunAgentPayload) => {
    setAgentSteps([]);
    setDone(null);
    setError(null);
    ws.current?.send(JSON.stringify({ type: 'run_agent', ...payload }));
  }, []);

  const sendChat = useCallback((payload: ChatPayload) => {
    setChatTokens('');
    ws.current?.send(JSON.stringify({ type: 'chat', ...payload }));
  }, []);

  return { connected, agentSteps, chatTokens, done, error, runAgent, sendChat };
}