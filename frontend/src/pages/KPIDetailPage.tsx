import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  TrendingUp, TrendingDown, ArrowLeft, AlertTriangle,
  Target, Shield, ChevronRight
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  BarChart, Bar, Cell
} from 'recharts';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatPercent, getChangeColor, getPriorityColor } from '../lib/utils';
import ConfidenceGauge from '../components/dashboard/ConfidenceGauge';
import type { Insight } from '../types';

export default function KPIDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [data, setData] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) loadData(id);
  }, [id, user?.role_name]);

  const loadData = async (kpiId: string) => {
    setLoading(true);
    try {
      const res = await api.getKPIDetail(kpiId, user?.role_name || 'CEO');
      setData(res);
    } catch {} finally { setLoading(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading...</div>;
  if (!data) return <div className="text-center text-slate-400 mt-20">KPI not found</div>;

  const trendData = (data.trend || []).map(d => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: d.value,
  }));

  const driverData = data.drivers.filter(d => d.contribution_percent >= 3).map(d => ({
    name: d.name.length > 20 ? d.name.substring(0, 20) + '...' : d.name,
    fullName: d.name,
    contribution: d.contribution_percent,
    color: d.contribution_percent > 30 ? '#ef4444' : d.contribution_percent > 15 ? '#f59e0b' : '#3b82f6',
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/" className="p-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 transition">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold">{data.kpi_name}</h1>
          <p className="text-xs text-slate-400">{data.kpi_description}</p>
        </div>
        {data.materiality && (
          <span className={`ml-2 text-[10px] px-2 py-1 rounded-full border ${getPriorityColor(data.materiality.priority)}`}>
            {data.materiality.priority}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-navy-800 rounded-xl p-4 card-glow">
          <p className="text-xs text-slate-400">Current Value</p>
          <p className="text-xl font-bold mt-1">{formatCurrency(data.current_value)}</p>
        </div>
        <div className="bg-navy-800 rounded-xl p-4 card-glow">
          <p className="text-xs text-slate-400">Previous Value</p>
          <p className="text-xl font-bold mt-1">{formatCurrency(data.previous_value)}</p>
        </div>
        <div className="bg-navy-800 rounded-xl p-4 card-glow">
          <p className="text-xs text-slate-400">Change</p>
          <div className="flex items-center gap-2 mt-1">
            {data.change_percent == null ? (
              <p className={`text-xl font-bold text-slate-400`}>No prior data</p>
            ) : (
              <>
                {data.change_percent >= 0 ? <TrendingUp className="w-5 h-5 text-green-400" /> : <TrendingDown className="w-5 h-5 text-red-400" />}
                <p className={`text-xl font-bold ${getChangeColor(data.change_percent)}`}>{formatPercent(data.change_percent)}</p>
              </>
            )}
          </div>
        </div>
        <ConfidenceGauge score={data.confidence.confidence_score} level={data.confidence.confidence_level} />
      </div>

      {data.abstention?.should_abstain && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h3 className="font-semibold text-red-400">INSUFFICIENT EVIDENCE</h3>
          </div>
          <p className="text-sm text-slate-300">{data.narrative}</p>
          <div className="mt-3 flex gap-2">
            {data.abstention.suggested_actions.filter(Boolean).map((action, i) => (
              <span key={i} className="text-xs bg-navy-900 rounded-lg px-3 py-1.5 text-slate-400">{action}</span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-4">Historical Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5ea" />
              <XAxis dataKey="date" tick={{ fill: '#6e6e73', fontSize: 10 }} />
              <YAxis tick={{ fill: '#6e6e73', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e5ea', borderRadius: '8px' }}
                labelStyle={{ color: '#1d1d1f' }}
              />
              <Line type="monotone" dataKey="value" stroke="#0071e3" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-4">Driver Decomposition</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={driverData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5ea" />
              <XAxis type="number" tick={{ fill: '#6e6e73', fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#3a3a3c', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e5ea', borderRadius: '8px', color: '#1d1d1f' }}
              />
              <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
                {driverData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-navy-800 rounded-xl p-5 card-glow">
        <h3 className="font-semibold text-sm mb-4">Drivers Ranked by Contribution</h3>
        <div className="space-y-3">
          {data.drivers.map(driver => (
            <div key={driver.name} className="flex items-center gap-4 p-3 bg-navy-900/50 rounded-lg hover:bg-navy-700/50 transition cursor-pointer">
              <span className="text-xs text-slate-500 w-6">#{driver.rank}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-300">{driver.name}</span>
                  {driver.is_primary && <span className="text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded-full">Primary</span>}
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">{driver.data_source} • Confidence: {(driver.confidence * 100).toFixed(0)}%</p>
              </div>
              <div className="w-32">
                <div className="h-2 bg-navy-900 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${Math.min(driver.contribution_percent, 100)}%`, backgroundColor: driver.contribution_percent > 30 ? '#ef4444' : '#3b82f6' }}
                  />
                </div>
              </div>
              <span className="text-sm font-bold text-slate-300 w-16 text-right">{driver.contribution_percent}%</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-4">Evidence</h3>
          <div className="space-y-3">
            {data.evidence.map((ev, i) => (
              <div key={i} className="bg-navy-900/50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-300">{ev.source}</span>
                  {ev.change_percent != null && (
                    <span className={`text-xs font-medium ${getChangeColor(ev.change_percent)}`}>
                      {formatPercent(ev.change_percent)}
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-500 mt-1">{ev.analytical_method}</p>
                {ev.data_lineage && (
                  <p className="text-[10px] text-slate-600 mt-0.5">
                    Lineage: {String((ev.data_lineage as Record<string, unknown>).source_system)} → {String((ev.data_lineage as Record<string, unknown>).operation)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-4">Recommendations</h3>
          <div className="space-y-3">
            {data.recommendations.map((rec, i) => (
              <div key={i} className="bg-navy-900/50 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <Target className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-slate-200">{rec.action}</p>
                    <div className="grid grid-cols-2 gap-2 mt-2 text-[10px] text-slate-500">
                      <span>Owner: {rec.owner}</span>
                      <span>Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                      <span>{rec.expected_impact}</span>
                      <span>Lever: {rec.lever}</span>
                    </div>
                    {rec.monitoring_plan && (
                      <p className="text-[10px] text-slate-600 mt-1.5">Monitor: {rec.monitoring_plan}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {data.narrative && (
        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-3">AI-Generated Narrative</h3>
          <div className="bg-navy-900/50 rounded-lg p-4 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
            {data.narrative}
          </div>
          <p className="text-[10px] text-slate-600 mt-2">LLM-generated narrative based on deterministic analytical results</p>
        </div>
      )}
    </div>
  );
}
