import React, { useEffect, useState } from 'react';
import { FileText, Download, Printer } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatPercent, getChangeColor } from '../lib/utils';
import type { Insight } from '../types';

export default function ReportsPage() {
  const { user } = useAuth();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [user?.role_name]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getInsights(user?.role_name || 'CEO');
      setInsights(res.insights.slice(0, 2));
    } catch {} finally { setLoading(false); }
  };

  if (loading) return <div className="text-center text-slate-400 py-20 text-sm">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Reports</h1>
          <p className="text-sm text-slate-400 mt-0.5">Generate business insight reports</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-3 py-2 bg-navy-800 border border-slate-700 rounded-lg text-xs text-slate-300 hover:border-accent transition">
            <Printer className="w-3.5 h-3.5" /> Print
          </button>
          <button className="flex items-center gap-2 px-3 py-2 gradient-accent rounded-lg text-xs text-white transition">
            <Download className="w-3.5 h-3.5" /> Export PDF
          </button>
        </div>
      </div>

      {insights.map(insight => (
        <div key={insight.kpi_name} className="bg-navy-800 rounded-xl p-6 card-glow">
          <div className="border-b border-slate-700/50 pb-4 mb-4">
            <div className="flex items-center gap-2 mb-1">
              <FileText className="w-4 h-4 text-accent" />
              <h2 className="font-semibold">Business Insight Report</h2>
            </div>
            <p className="text-xs text-slate-500">ShopSmart Analytics • {new Date().toLocaleDateString()}</p>
          </div>

          <div className="mb-4">
            <h3 className="text-xs font-medium text-slate-400 mb-1">EXECUTIVE SUMMARY</h3>
            <p className="text-sm text-slate-300">{insight.change_percent != null
                ? `${insight.kpi_name} ${insight.change_percent >= 0 ? 'increased' : 'decreased'} by ${Math.abs(insight.change_percent).toFixed(1)}% in the current period${insight.change_percent != null ? '' : ''}.`
                : `Full data period (no prior baseline available) for ${insight.kpi_name}.`}</p>
            <p className="text-sm text-slate-300 mt-1">
              Current value: {formatCurrency(insight.current_value)} | Previous: {formatCurrency(insight.previous_value)}
            </p>
          </div>

          <div className="mb-4">
            <h3 className="text-xs font-medium text-slate-400 mb-2">DRIVERS</h3>
            <div className="space-y-1.5">
              {insight.drivers.filter(d => d.contribution_percent >= 5).map(d => (
                <div key={d.name} className="flex items-center gap-2 text-xs">
                  <span className="text-slate-300 w-48">{d.name}</span>
                  <span className={`font-medium ${getChangeColor(d.change_percent || 0)}`}>
                    {d.contribution_percent}% contribution
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <h3 className="text-xs font-medium text-slate-400 mb-2">EVIDENCE</h3>
            {insight.evidence.map((ev, i) => (
              <div key={i} className="flex items-center gap-2 text-xs mb-1">
                <span className="text-slate-400">{ev.source}:</span>
                <span className="text-slate-300">{ev.analytical_method}</span>
                {ev.change_percent != null && <span className={getChangeColor(ev.change_percent)}>{formatPercent(ev.change_percent)}</span>}
              </div>
            ))}
          </div>

          <div className="mb-4">
            <h3 className="text-xs font-medium text-slate-400 mb-2">CONFIDENCE: {insight.confidence.confidence_score}%</h3>
            <p className="text-xs text-slate-400">
              {insight.confidence.confidence_level === 'high' ? 'Analysis is well-supported by available data.' :
               insight.confidence.confidence_level === 'medium' ? 'Some evidence gaps exist.' : 'Insufficient evidence for confident conclusions.'}
            </p>
          </div>

          <div>
            <h3 className="text-xs font-medium text-slate-400 mb-2">RECOMMENDATIONS</h3>
            {insight.recommendations.map((rec, i) => (
              <div key={i} className="text-xs mb-2">
                <p className="text-slate-300">{rec.action}</p>
                <p className="text-slate-500">Owner: {rec.owner} | Impact: {rec.expected_impact}</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
