import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp, TrendingDown, Activity, AlertTriangle, Target,
  ArrowRight, ChevronRight, Shield, Lightbulb
} from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatPercent, getChangeColor, getPriorityColor, getConfidenceColor } from '../lib/utils';
import type { KPICard, Insight } from '../types';
import ConfidenceGauge from '../components/dashboard/ConfidenceGauge';

export default function OverviewPage() {
  const { user } = useAuth();
  const [kpiCards, setKpiCards] = useState<KPICard[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [user?.role_name]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpisRes, insightsRes] = await Promise.all([
        api.getKPIs(user?.role_name || 'CEO'),
        api.getInsights(user?.role_name || 'CEO'),
      ]);
      setKpiCards(kpisRes.kpi_cards);
      setInsights(insightsRes.insights);
    } catch {} finally {
      setLoading(false);
    }
  };

  const primaryInsight = insights.find(i => i.materiality?.priority === 'CRITICAL' || i.materiality?.priority === 'HIGH');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400 text-sm">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Overview</h1>
          <p className="text-sm text-slate-400 mt-0.5">ShopSmart Intelligence Dashboard</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">Persona: {user?.role_name}</p>
          <p className="text-xs text-slate-400">Current data period</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {kpiCards.map(kpi => (
          <Link
            key={kpi.id}
            to={`/kpis/${kpi.id}`}
            className={`bg-navy-800 rounded-xl p-4 card-glow hover:border-accent/30 transition-all group ${kpi.priority !== 'NONE' && kpi.priority !== 'LOW' ? 'border-l-2 ' + ((kpi.change_percent ?? 0) < 0 ? 'border-l-red-500' : 'border-l-green-500') : ''}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400">{kpi.name}</span>
              {kpi.priority && kpi.priority !== 'NONE' && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${getPriorityColor(kpi.priority)}`}>
                  {kpi.priority}
                </span>
              )}
            </div>
            <p className="text-lg font-bold">
              {kpi.id === 'conversion_rate' || kpi.id === 'marketing_roi'
                ? kpi.value.toFixed(2)
                : formatCurrency(kpi.value)}
            </p>
            <div className="flex items-center gap-1.5 mt-1">
              {kpi.change_percent == null ? (
                <span className="text-xs font-medium text-slate-400">No prior period data</span>
              ) : (
                <>
                  {kpi.change_percent >= 0 ? (
                    <TrendingUp className="w-3.5 h-3.5 text-green-400" />
                  ) : (
                    <TrendingDown className="w-3.5 h-3.5 text-red-400" />
                  )}
                  <span className={`text-xs font-medium ${getChangeColor(kpi.change_percent)}`}>
                    {formatPercent(kpi.change_percent)}
                  </span>
                  <span className="text-[10px] text-slate-500">vs prev period</span>
                </>
              )}
            </div>
            {kpi.trend && kpi.trend.length > 0 && (
              <div className="mt-3 h-8 flex items-end gap-px">
                {kpi.trend.slice(-14).map((v, i) => {
                  const max = Math.max(...kpi.trend.slice(-14));
                  const min = Math.min(...kpi.trend.slice(-14));
                  const range = max - min || 1;
                  const h = ((v - min) / range) * 100;
                  return (
                    <div
                      key={i}
                      className="flex-1 rounded-sm"
                      style={{
                        height: `${Math.max(4, h)}%`,
                        backgroundColor: kpi.has_prior
                          ? v >= (kpi.previous_value / 14) ? 'rgba(34,197,94,0.4)' : 'rgba(239,68,68,0.4)'
                          : 'rgba(59,130,246,0.4)',
                      }}
                    />
                  );
                })}
              </div>
            )}
          </Link>
        ))}
      </div>

      {primaryInsight && (
        <div className="bg-navy-800 rounded-xl p-6 card-glow">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <div>
              <h2 className="font-semibold">Key Insight</h2>
              <p className="text-xs text-slate-400">Requires attention</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-navy-900/50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-slate-300 mb-1">
                  {primaryInsight.change_percent != null
                    ? `${primaryInsight.kpi_name} ${primaryInsight.change_percent >= 0 ? 'increased' : 'declined'} ${Math.abs(primaryInsight.change_percent).toFixed(1)}%`
                    : `${primaryInsight.kpi_name} requires attention (full data period, no prior baseline)`}
                </h3>
                <p className="text-xs text-slate-400">
                  Current: {formatCurrency(primaryInsight.current_value)} | Previous: {formatCurrency(primaryInsight.previous_value)}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-medium text-slate-400 mb-2">DRIVER CONTRIBUTION</h4>
                <div className="space-y-2">
                  {primaryInsight.drivers.filter(d => d.contribution_percent >= 5).slice(0, 5).map(driver => (
                    <div key={driver.name} className="flex items-center gap-3">
                      <span className="text-xs text-slate-300 w-40 truncate">{driver.name}</span>
                      <div className="flex-1 h-5 bg-navy-900 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(driver.contribution_percent, 100)}%`,
                            backgroundColor: driver.contribution_percent > 30 ? '#ef4444' :
                              driver.contribution_percent > 15 ? '#f59e0b' : '#3b82f6',
                          }}
                        />
                      </div>
                      <span className="text-xs font-medium text-slate-300 w-12 text-right">
                        {driver.contribution_percent}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {primaryInsight.recommendations.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-xs font-medium text-slate-400 mb-2">RECOMMENDED ACTIONS</h4>
                  <div className="space-y-2">
                    {primaryInsight.recommendations.slice(0, 3).map((rec, i) => (
                      <div key={i} className="flex items-start gap-2 bg-navy-900/50 rounded-lg p-3">
                        <Target className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="text-xs text-slate-200">{rec.action}</p>
                          <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-500">
                            <span>Owner: {rec.owner}</span>
                            <span>{rec.expected_impact}</span>
                          </div>
                        </div>
                        <Link to="/recommendations" className="text-accent hover:text-accent-light transition">
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <ConfidenceGauge score={primaryInsight.confidence.confidence_score} level={primaryInsight.confidence.confidence_level} />

              <div className="bg-navy-900/50 rounded-lg p-4">
                <h4 className="text-xs font-medium text-slate-400 mb-2">EVIDENCE SOURCES</h4>
                <div className="space-y-2">
                  {primaryInsight.evidence.slice(0, 4).map((ev, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{ev.source}</span>
                      <span className={`${getChangeColor(ev.change_percent || 0)}`}>
                        {ev.change_percent != null ? formatPercent(ev.change_percent) : 'N/A'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-navy-900/50 rounded-lg p-4">
                <h4 className="text-xs font-medium text-slate-400 mb-2">DATA SOURCES</h4>
                <div className="space-y-1.5">
                  {primaryInsight.data_sources.map(src => (
                    <div key={src} className="flex items-center gap-2 text-xs">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                      <span className="text-slate-300 capitalize">{src}</span>
                    </div>
                  ))}
                </div>
              </div>

              {primaryInsight.contradictions?.has_contradictions && (
                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Shield className="w-4 h-4 text-yellow-400" />
                    <span className="text-xs font-medium text-yellow-400">Contradictory Evidence</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Multiple explanations remain plausible</p>
                </div>
              )}

              {primaryInsight.abstention?.should_abstain && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                    <span className="text-xs font-medium text-red-400">INSUFFICIENT EVIDENCE</span>
                  </div>
                  <p className="text-[10px] text-slate-400">{primaryInsight.abstention.reasons.join('; ')}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm">All Insights</h3>
            <Link to="/insights" className="text-xs text-accent hover:text-accent-light flex items-center gap-1 transition">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {insights.slice(0, 4).map(insight => (
              <Link
                key={insight.kpi_name}
                to={`/kpis/${insight.kpi_name}`}
                className="flex items-center justify-between p-3 bg-navy-900/50 rounded-lg hover:bg-navy-700/50 transition"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${insight.change_percent == null ? 'bg-blue-400' : insight.change_percent < 0 ? 'bg-red-400' : 'bg-green-400'}`} />
                  <div>
                    <p className="text-xs font-medium text-slate-200">{insight.kpi_name}</p>
                    <p className="text-[10px] text-slate-500">{insight.drivers.length} drivers identified</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-xs font-medium ${getChangeColor(insight.change_percent)}`}>
                    {formatPercent(insight.change_percent)}
                  </p>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${getPriorityColor(insight.materiality?.priority)}`}>
                    {insight.materiality?.priority}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="bg-navy-800 rounded-xl p-5 card-glow">
          <h3 className="font-semibold text-sm mb-4">Architecture Overview</h3>
          <div className="space-y-3 text-xs text-slate-400">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] text-blue-400">1</span>
              </div>
              <div>
                <p className="text-slate-200 font-medium">Data Ingestion</p>
                <p className="text-[10px]">3 sources: Sales, Marketing, Inventory</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] text-green-400">2</span>
              </div>
              <div>
                <p className="text-slate-200 font-medium">Deterministic Analysis</p>
                <p className="text-[10px]">KPIs, Anomaly Detection, Driver Analysis</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-yellow-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] text-yellow-400">3</span>
              </div>
              <div>
                <p className="text-slate-200 font-medium">Confidence & Evidence</p>
                <p className="text-[10px]">Multi-source corroboration, abstention logic</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] text-purple-400">4</span>
              </div>
              <div>
                <p className="text-slate-200 font-medium">LLM Narrative</p>
                <p className="text-[10px]">Persona-specific explanation generation</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] text-red-400">5</span>
              </div>
              <div>
                <p className="text-slate-200 font-medium">Recommendations</p>
                <p className="text-[10px]">Grounded actions with owners and impact</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
