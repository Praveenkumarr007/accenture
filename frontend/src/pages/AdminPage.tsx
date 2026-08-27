import React, { useEffect, useState } from 'react';
import { Users, Database, Activity, Settings, Cpu, Gauge } from 'lucide-react';
import { api } from '../lib/api';
import type { TelemetryData, User } from '../types';

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersRes, telRes] = await Promise.all([
        api.getAdminUsers().catch(() => ({ users: [] })),
        api.getTelemetry(),
      ]);
      setUsers(usersRes.users);
      setTelemetry(telRes);
    } catch {} finally { setLoading(false); }
  };

  if (loading) return <div className="text-center text-slate-400 py-20 text-sm">Loading...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Admin</h1>
        <p className="text-sm text-slate-400 mt-0.5">System administration and monitoring</p>
      </div>

      {telemetry && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="w-4 h-4 text-accent" />
              <span className="text-[10px] text-slate-400">AVG LATENCY</span>
            </div>
            <p className="text-lg font-bold">{telemetry.average_latency_ms.toFixed(0)}ms</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span className="text-[10px] text-slate-400">LLM CALLS</span>
            </div>
            <p className="text-lg font-bold">{telemetry.total_llm_calls}</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-green-400" />
              <span className="text-[10px] text-slate-400">TOKENS</span>
            </div>
            <p className="text-lg font-bold">{telemetry.total_tokens.toLocaleString()}</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] text-slate-400">EST. COST</span>
            </div>
            <p className="text-lg font-bold text-green-400">${telemetry.estimated_cost.toFixed(4)}</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] text-slate-400">SUCCESS RATE</span>
            </div>
            <p className="text-lg font-bold">{telemetry.success_rate}%</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] text-slate-400">FAILED</span>
            </div>
            <p className="text-lg font-bold text-red-400">{telemetry.failed_requests}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-4 h-4 text-accent" />
            <h3 className="font-semibold text-sm">Users</h3>
          </div>
          <div className="space-y-2">
            {users.map(u => (
              <div key={u.id} className="flex items-center justify-between p-3 bg-navy-900/50 rounded-lg">
                <div>
                  <p className="text-xs font-medium text-slate-200">{u.full_name || u.username}</p>
                  <p className="text-[10px] text-slate-500">{u.username} • {u.email}</p>
                </div>
                <span className="text-[10px] px-2 py-0.5 bg-accent/20 text-accent rounded-full">{u.role_name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <div className="flex items-center gap-2 mb-4">
            <Settings className="w-4 h-4 text-accent" />
            <h3 className="font-semibold text-sm">System Configuration</h3>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between p-2 bg-navy-900/50 rounded-lg">
              <span className="text-slate-400">Application</span>
              <span className="text-slate-200">BusinessIntelligence.AI v1.0.0</span>
            </div>
            <div className="flex justify-between p-2 bg-navy-900/50 rounded-lg">
              <span className="text-slate-400">Demo Mode</span>
              <span className="text-green-400">Active</span>
            </div>
            <div className="flex justify-between p-2 bg-navy-900/50 rounded-lg">
              <span className="text-slate-400">LLM Enabled</span>
              <span className="text-yellow-400">Disabled (using deterministic narratives)</span>
            </div>
            <div className="flex justify-between p-2 bg-navy-900/50 rounded-lg">
              <span className="text-slate-400">Database</span>
              <span className="text-slate-200">SQLite</span>
            </div>
            <div className="flex justify-between p-2 bg-navy-900/50 rounded-lg">
              <span className="text-slate-400">Auth</span>
              <span className="text-slate-200">JWT + RBAC</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
