'use client';
import { useEffect } from 'react';
import { useAgentStream } from '../../../hooks/useAgentStream';

const statusIcon = { started: '⏳', running: '⚙️', completed: '✅', failed: '❌' };
const statusBg = {
  started: 'bg-yellow-900/20 border-yellow-800',
  running: 'bg-blue-900/20 border-blue-800',
  completed: 'bg-green-900/20 border-green-800',
  failed: 'bg-red-900/20 border-red-800',
};
const statusText = {
  started: 'text-yellow-400',
  running: 'text-blue-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
};

export default function AgentStreamPanel({ sessionId, onDone }) {
  const { connected, agentSteps, chatTokens, done, error, runAgent } = useAgentStream(sessionId);

  useEffect(() => {
    if (done && onDone) onDone(done);
  }, [done, onDone]);

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-700 font-mono text-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
        <span className="text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
      </div>

      {agentSteps.length === 0 && (
        <p className="text-gray-500 text-center py-8">Waiting for agents to start...</p>
      )}

      <div className="space-y-3">
        {agentSteps.map((step, i) => (
          <div key={i} className={`flex items-start gap-3 p-3 rounded-lg ${statusBg[step.status]}`}>
            <span className="text-lg">{statusIcon[step.status] || '🤖'}</span>
            <div className="flex-1">
              <p className={`font-bold ${statusText[step.status]}`}>{step.agent}</p>
              <p className="text-gray-300 text-xs mt-1">{step.message}</p>
            </div>
          </div>
        ))}
      </div>

      {chatTokens && (
        <div className="mt-4 p-3 bg-gray-800 rounded-lg">
          <p className="text-green-300">{chatTokens}<span className="animate-pulse">▋</span></p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-900/30 border border-red-700 rounded-lg">
          <p className="text-red-400">❌ {error}</p>
        </div>
      )}

      {done && (
        <div className="mt-4 p-3 bg-green-900/20 border border-green-700 rounded-lg">
          <p className="text-green-400 font-bold">🎉 All agents completed!</p>
        </div>
      )}
    </div>
  );
}