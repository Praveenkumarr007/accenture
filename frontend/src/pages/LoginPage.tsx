import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Eye, EyeOff } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';

export default function LoginPage() {
  const [username, setUsername] = useState('ceo');
  const [password, setPassword] = useState('demo123');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.login(username, password);
      login(res.user, res.access_token);
      navigate('/');
    } catch {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl gradient-accent flex items-center justify-center mx-auto mb-4">
            <Zap className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold">BusinessIntelligence.AI</h1>
          <p className="text-slate-400 text-sm mt-1">KPI Intelligence → Evidence → Action</p>
        </div>

        <div className="bg-navy-800 rounded-2xl p-6 card-glow">
          <h2 className="text-lg font-semibold mb-4">Sign In</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full bg-navy-700 border border-slate-600 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-accent transition"
                placeholder="Enter username"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Password</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-navy-700 border border-slate-600 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-accent transition pr-10"
                  placeholder="Enter password"
                />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full gradient-accent rounded-lg py-2.5 text-sm font-medium disabled:opacity-50 transition"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-700/50">
            <p className="text-xs text-slate-500 mb-2">Demo Accounts:</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                { user: 'ceo', pass: 'demo123', role: 'CEO' },
                { user: 'sales_mgr', pass: 'demo123', role: 'Sales Mgr' },
                { user: 'marketing_mgr', pass: 'demo123', role: 'Marketing Mgr' },
                { user: 'admin', pass: 'admin123', role: 'Admin' },
              ].map(a => (
                <button
                  key={a.user}
                  onClick={() => { setUsername(a.user); setPassword(a.pass); }}
                  className="px-2 py-1.5 bg-navy-700 rounded-lg text-slate-400 hover:text-white hover:bg-navy-600 transition"
                >
                  {a.role}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
