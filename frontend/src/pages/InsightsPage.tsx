import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Lightbulb, AlertTriangle, ChevronRight } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatPercent, getChangeColor, getPriorityColor } from '../lib/utils';
import type { Insight } from '../types';

export default function InsightsPage() {
  const { user } = useAuth();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [user?.role_name]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getInsights(user?.role_name || 'CEO');
      setInsights(res.insights);
    } catch {} finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Insights</h1>
        <p className="text-sm text-slate-400 mt-0.5">All detected KPI movements and their analysis</p>
      </div>

      {loading ? (
        <div className="text-center text-slate-400 py-20 text-sm">Loading insights...</div>
      ) : (
        <div className="space-y-4">
          {insights.map(insight => (
            <Link
              key={insight.kpi_name}
              to={`/kpis/${insight.kpi_name}`}
              className="block bg-navy-800 rounded-xl p-5 card-glow hover:border-accent/20 transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${insight.change_percent == null ? 'bg-blue-500/20' : insight.change_percent < 0 ? 'bg-red-500/20' : 'bg-green-500/20'}`}>
                    {insight.materiality?.priority === 'CRITICAL' || insight.materiality?.priority === 'HIGH' ? (
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                    ) : (
                      <Lightbulb className="w-5 h-5 text-accent" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-sm">{insight.kpi_name}</h3>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${getPriorityColor(insight.materiality?.priority)}`}>
                        {insight.materiality?.priority}
                      </span>
                      {insight.abstention?.should_abstain && (
                        <span className="text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded-full">ABSTAINED</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{insight.kpi_description}</p>
                  </div>
                </div>
                <div className="text-right flex items-center gap-4">
                  <div>
                    <p className="text-lg font-bold">{formatCurrency(insight.current_value)}</p>
                    <p className={`text-xs font-medium ${getChangeColor(insight.change_percent)}`}>
                      {formatPercent(insight.change_percent)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Confidence</p>
                    <p className={`text-sm font-bold ${
                      insight.confidence.confidence_score >= 80 ? 'text-green-400' :
                      insight.confidence.confidence_score >= 50 ? 'text-yellow-400' : 'text-red-400'
                    }`}>{insight.confidence.confidence_score}%</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-600" />
                </div>
              </div>

              <div className="mt-4 flex items-center gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    {insight.drivers.slice(0, 3).map(d => (
                      <div key={d.name} className="flex items-center gap-1 bg-navy-900/50 rounded-lg px-2 py-1">
                        <span className="text-[10px] text-slate-400">{d.name}</span>
                        <span className="text-[10px] font-bold text-slate-200">{d.contribution_percent}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                {insight.contradictions?.has_contradictions && (
                  <span className="text-[10px] text-yellow-400 bg-yellow-500/10 px-2 py-1 rounded-full">Contradictory evidence</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
