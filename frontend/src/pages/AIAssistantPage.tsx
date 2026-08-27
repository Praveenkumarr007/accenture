import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import { Bot, Send, User, Zap, Database, Shield } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  tokens?: number;
  cost?: number;
}

export default function AIAssistantPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `Hello ${user?.full_name || 'User'}. I'm your Business Intelligence assistant for ShopSmart. I can help you understand KPI movements, their drivers, and recommended actions.\n\nTry asking:\n- "Why did revenue decline?"\n- "What caused the change?"\n- "Which product contributed the most?"\n- "What should I do?"`,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.sendAssistantMessage(input);
      const assistantMsg: Message = {
        role: 'assistant',
        content: res.response,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I apologize, but I encountered an error processing your request. Please try again.',
        },
      ]);
    }
    setLoading(false);
  };

  const quickQuestions = [
    'Why did revenue decline?',
    'What are the main drivers?',
    'What should I do next?',
    'Show me marketing analysis',
    'Why is confidence low?',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Bot size={24} className="text-blue-400" /> AI Assistant
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Ask questions about KPI movements, drivers, and recommendations
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-4 bg-navy-800/30 rounded-xl border border-slate-700/30">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Bot size={14} className="text-white" />
              </div>
            )}
            <div className={`max-w-[70%] p-3 rounded-xl ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-navy-700/50 border border-slate-700/30 text-slate-200'
            }`}>
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              {msg.model && msg.model !== 'fallback' && (
                <div className="flex items-center gap-3 mt-2 pt-2 border-t border-slate-700/30 text-[10px] text-slate-500">
                  <span className="flex items-center gap-1"><Zap size={10} /> {msg.model}</span>
                  <span>{msg.tokens} tokens</span>
                  <span>${msg.cost?.toFixed(4)}</span>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                <User size={14} className="text-slate-300" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
              <Bot size={14} className="text-white" />
            </div>
            <div className="bg-navy-700/50 border border-slate-700/30 rounded-xl p-3">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                Analyzing...
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {quickQuestions.map((q) => (
          <button
            key={q}
            onClick={() => setInput(q)}
            className="px-3 py-1.5 bg-navy-700/30 border border-slate-700/30 rounded-full text-xs text-slate-400 hover:text-slate-200 hover:border-blue-500/30 transition-all"
          >
            {q}
          </button>
        ))}
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about KPI movements, drivers, or recommendations..."
          className="input flex-1"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="btn btn-primary px-4"
        >
          <Send size={16} />
        </button>
      </div>

      <div className="mt-2 flex items-center gap-4 text-[10px] text-slate-600">
        <span className="flex items-center gap-1"><Shield size={8} /> LLM guardrails active</span>
        <span className="flex items-center gap-1"><Database size={8} /> Evidence-backed responses</span>
        <span className="flex items-center gap-1"><Zap size={8} /> Never invents data</span>
      </div>
    </div>
  );
}
