import React, { useState } from 'react';
import { Bell, User, ChevronDown, Monitor } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../lib/api';

const personas = ['CEO', 'Sales Manager', 'Marketing Manager'];

export default function TopNav() {
  const { user, switchPersona } = useAuth();
  const [showPersona, setShowPersona] = useState(false);
  const [activeScenario, setActiveScenario] = useState<string | null>(null);

  const handleScenario = async (scenario: string) => {
    try {
      const res = await api.switchScenario(scenario);
      setActiveScenario(scenario);
      window.dispatchEvent(new CustomEvent('scenario-switch', { detail: res }));
    } catch {}
  };

  return (
    <header className="h-14 bg-navy-800/80 border-b border-slate-700/50 flex items-center px-6 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-white">BusinessIntelligence.AI</h1>
        <span className="text-[10px] px-2 py-0.5 bg-accent/20 text-accent-light rounded-full">Demo Mode</span>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        <div className="flex items-center gap-1 mr-3">
          <Monitor className="w-3.5 h-3.5 text-slate-500" />
          <select
            onChange={e => handleScenario(e.target.value)}
            value={activeScenario || ''}
            className="bg-navy-700 border border-slate-600 rounded-lg px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-accent"
          >
            <option value="">Select Scenario</option>
            <option value="major_decline">Major Revenue Decline</option>
            <option value="low_confidence">Low Confidence</option>
            <option value="sparse_history">Sparse History</option>
            <option value="contradictory">Contradictory Evidence</option>
            <option value="access_restriction">Access Restriction</option>
          </select>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowPersona(!showPersona)}
            className="flex items-center gap-2 bg-navy-700 border border-slate-600 rounded-lg px-3 py-1.5 text-xs text-slate-300 hover:border-accent transition"
          >
            <User className="w-3.5 h-3.5" />
            <span>{user?.role_name || 'CEO'}</span>
            <ChevronDown className="w-3 h-3" />
          </button>
          {showPersona && (
            <div className="absolute right-0 top-full mt-1 bg-navy-700 border border-slate-600 rounded-lg shadow-xl z-50 w-48 py-1">
              <p className="px-3 py-1 text-[10px] text-slate-500 uppercase tracking-wider">Switch Persona</p>
              {personas.map(p => (
                <button
                  key={p}
                  onClick={() => { switchPersona(p); setShowPersona(false); }}
                  className={`w-full text-left px-3 py-1.5 text-xs hover:bg-accent/10 transition ${
                    user?.role_name === p ? 'text-accent-light' : 'text-slate-300'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>

        <button className="relative p-2 text-slate-400 hover:text-white transition">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
      </div>
    </header>
  );
}
