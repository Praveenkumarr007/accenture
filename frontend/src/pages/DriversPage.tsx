import React, { useEffect, useState } from 'react';
import { GitBranch } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import type { Driver } from '../types';

export default function DriversPage() {
  const { user } = useAuth();
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [kpiName, setKpiName] = useState('revenue');
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadDrivers(); }, [kpiName, user?.role_name]);

  const loadDrivers = async () => {
    setLoading(true);
    try {
      const res = await api.getKPIDrivers(kpiName, user?.role_name || 'CEO');
      setDrivers(res.drivers);
    } catch {} finally { setLoading(false); }
  };

  const chartData = drivers.filter(d => d.contribution_percent >= 3).map(d => ({
    name: d.name.length > 18 ? d.name.substring(0, 18) + '...' : d.name,
    contribution: d.contribution_percent,
    color: d.contribution_percent > 30 ? '#ef4444' : d.contribution_percent > 15 ? '#f59e0b' : '#3b82f6',
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Driver Analysis</h1>
          <p className="text-sm text-slate-400 mt-0.5">Multi-factor decomposition of KPI movements</p>
        </div>
        <select
          value={kpiName}
          onChange={e => setKpiName(e.target.value)}
          className="bg-navy-700 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-accent"
        >
          <option value="revenue">Revenue</option>
          <option value="orders">Orders</option>
          <option value="aov">Average Order Value</option>
          <option value="conversion_rate">Conversion Rate</option>
          <option value="marketing_roi">Marketing ROI</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-4">Contribution Chart</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5ea" />
              <XAxis type="number" tick={{ fill: '#6e6e73', fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={150} tick={{ fill: '#3a3a3c', fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e5ea', borderRadius: '8px', color: '#1d1d1f' }} />
              <Bar dataKey="contribution" radius={[0, 4, 4, 0]} barSize={20}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-4">Driver Ranking</h3>
          <div className="space-y-2">
            {drivers.map(driver => (
              <div key={driver.name} className="flex items-center gap-3 p-3 bg-navy-900/50 rounded-lg">
                <span className="text-xs text-slate-500 w-6">#{driver.rank}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-300">{driver.name}</span>
                    {driver.is_primary && <span className="text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded-full">Primary</span>}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-500">
                    <span>Type: {driver.type}</span>
                    <span>Source: {driver.data_source}</span>
                    <span>Confidence: {(driver.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="w-24">
                  <div className="h-2 bg-navy-900 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${Math.min(driver.contribution_percent, 100)}%`, backgroundColor: driver.contribution_percent > 30 ? '#ef4444' : '#3b82f6' }}
                    />
                  </div>
                </div>
                <span className="text-sm font-bold text-slate-300 w-14 text-right">{driver.contribution_percent}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
