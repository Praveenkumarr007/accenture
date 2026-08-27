import React, { useState, useCallback, useRef } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { api } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';
import type { AssistantMessage } from '../../types';

export default function AIAssistant() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; evidence?: AssistantMessage['evidence_used'] }>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = useCallback(async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const res = await api.sendAssistantMessage(msg, user?.role_name || 'CEO');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.response,
        evidence: res.evidence_used,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'AI narrative unavailable. Quantitative analysis is still available.',
      }]);
    } finally {
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  }, [input, loading, user]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 p-4 border-b border-slate-700/50">
        <Bot className="w-5 h-5 text-accent" />
        <h3 className="font-semibold">AI Assistant</h3>
        <span className="text-xs text-slate-500 ml-auto">Evidence-backed analysis</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 mt-20">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Ask me about KPI changes, drivers, or recommendations.</p>
            <div className="mt-4 space-y-2 text-xs">
              <button onClick={() => setInput('Why did revenue decline?')} className="block mx-auto px-3 py-1.5 bg-navy-700 rounded-lg hover:bg-navy-600 transition">
                "Why did revenue decline?"
              </button>
              <button onClick={() => setInput('What are the top drivers?')} className="block mx-auto px-3 py-1.5 bg-navy-700 rounded-lg hover:bg-navy-600 transition">
                "What are the top drivers?"
              </button>
              <button onClick={() => setInput('What should I do?')} className="block mx-auto px-3 py-1.5 bg-navy-700 rounded-lg hover:bg-navy-600 transition">
                "What should I do?"
              </button>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full gradient-accent flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
            )}
            <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === 'user'
                ? 'bg-accent/20 text-accent-light'
                : 'bg-navy-700 text-slate-200'
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.evidence && msg.evidence.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-600/30 text-xs text-slate-400">
                  <p className="font-medium mb-1">Evidence consulted:</p>
                  {msg.evidence.map((e, j) => (
                    <p key={j}>• {e.source}: {e.metric} ({e.change >= 0 ? '+' : ''}{e.change?.toFixed(1)}%)</p>
                  ))}
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-navy-600 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full gradient-accent flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-navy-700 rounded-xl px-4 py-3 text-sm text-slate-400">
              Analyzing...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-slate-700/50">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask about KPIs, drivers, or recommendations..."
            className="flex-1 bg-navy-700 border border-slate-600 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-accent transition"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-2.5 gradient-accent rounded-lg disabled:opacity-50 transition"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-2">LLM generates narratives. All calculations are deterministic.</p>
      </div>
    </div>
  );
}
