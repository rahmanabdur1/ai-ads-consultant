'use client';

import { useState, KeyboardEvent } from 'react';
import { AxiosError } from 'axios';
import { agentAPI } from '../../src/lib/api';

// ==============================
// TYPES
// ==============================
type Role = 'user' | 'assistant' | 'error';

interface Message {
  role: Role;
  content: string;
}

interface ChatResponse {
  reply: string;
}

// ==============================
// COMPONENT
// ==============================
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const sendMessage = async (): Promise<void> => {
    if (!input.trim()) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);

    setInput('');
    setLoading(true);

    try {
      const workspace_id =
        typeof window !== 'undefined'
          ? localStorage.getItem('workspace_id')
          : null;

      const res = await agentAPI.chat({
        message: input,
        session_id: 'session-1',
        workspace_id: workspace_id || '',
      });

      const data = res.data as ChatResponse;

      const botMsg: Message = {
        role: 'assistant',
        content: data.reply,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const error = err as AxiosError;

      const errorMsg: Message = {
        role: 'error',
        content:
          'Error: ' +
          (error.response?.data
            ? JSON.stringify(error.response.data)
            : error.message),
      };

      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') sendMessage();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-4 rounded-lg max-w-3xl ${
              m.role === 'user'
                ? 'bg-blue-700 ml-auto'
                : m.role === 'error'
                ? 'bg-red-600'
                : 'bg-gray-700'
            }`}
          >
            <p className="text-xs text-gray-300 mb-1">
              {m.role === 'user'
                ? 'You'
                : m.role === 'assistant'
                ? 'AI Consultant'
                : 'Error'}
            </p>
            <p>{m.content}</p>
          </div>
        ))}

        {loading && (
          <div className="bg-gray-700 p-4 rounded-lg">
            Thinking...
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-700 flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Try: "Create a $500 campaign for my online store..."'
          className="flex-1 bg-gray-800 rounded-lg px-4 py-3 outline-none"
        />

        <button
          onClick={sendMessage}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-bold disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}