import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import type { KPICard } from '../types';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { formatPercent } from '../lib/utils';

export default function KPIMonitorPage() {
  const { persona } = useAuth();
  const navigate = useNavigate();
  const [kpis, setKpis] = useState<KPICard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getKPIs(persona).then(res => setKpis(res.kpi_cards)).catch(console.error).finally(() => setLoading(false));
  }, [persona]);

  const formatValue = (v: number) => {
    if (v >= 100000) return `$${(v / 100000).toFixed(1)}L`;
    return v.toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-foreground">KPI Monitor</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Track all key performance indicators</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3,4,5].map(i => <div key={i} className="h-40 bg-secondary rounded-2xl animate-pulse" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {kpis.map((kpi) => (
            <button
              key={kpi.id}
              onClick={() => navigate(`/kpi/${kpi.id}`)}
              className="bg-card rounded-2xl border border-border p-5 text-left hover:border-primary/30 transition-all"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-muted-foreground uppercase tracking-wider">{kpi.name}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                  kpi.priority === 'critical' || kpi.priority === 'high'
                    ? 'bg-destructive/10 text-destructive'
                    : kpi.priority === 'medium'
                    ? 'bg-yellow-500/10 text-yellow-500'
                    : 'bg-positive/10 text-positive'
                }`}>{kpi.priority.toUpperCase()}</span>
              </div>
              <div className="text-2xl font-bold text-foreground mb-2">{formatValue(kpi.value)}</div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {kpi.change_percent == null ? (
                    <span className="text-sm font-medium text-muted-foreground">{formatPercent(kpi.change_percent)}</span>
                  ) : kpi.change_percent < 0 ? (
                    <>
                      <TrendingDown size={14} className="text-destructive" />
                      <span className={`text-sm font-medium text-destructive`}>
                        {formatPercent(kpi.change_percent)}
                      </span>
                    </>
                  ) : (
                    <>
                      <TrendingUp size={14} className="text-positive" />
                      <span className={`text-sm font-medium text-positive`}>
                        {formatPercent(kpi.change_percent)}
                      </span>
                    </>
                  )}
                </div>
                <span className="text-[10px] text-muted-foreground">{kpi.change_percent == null ? 'Full-period data' : 'period change'}</span>
              </div>
              <div className="mt-3 pt-3 border-t border-border flex items-center gap-1">
                <Activity size={10} className="text-muted-foreground" />
                <span className="text-[10px] text-muted-foreground">Click to view details</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
