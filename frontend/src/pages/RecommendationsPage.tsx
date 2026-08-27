import React, { useEffect, useState } from 'react';
import { Target, Shield, Clock } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency } from '../lib/utils';
import type { Recommendation } from '../types';

export default function RecommendationsPage() {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [user?.role_name]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getRecommendations(user?.role_name || 'CEO');
      setRecommendations(res.recommendations);
    } catch {} finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Recommendations</h1>
        <p className="text-sm text-slate-400 mt-0.5">Actionable recommendations grounded in detected drivers</p>
      </div>

      {loading ? (
        <div className="text-center text-slate-400 py-20 text-sm">Loading...</div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec, i) => (
            <div key={i} className="bg-navy-800 rounded-xl p-5 card-glow">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg gradient-accent flex items-center justify-center flex-shrink-0">
                  <Target className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-slate-400">Driver: {rec.driver_name}</span>
                    {rec.kpi_name && <span className="text-[10px] px-1.5 py-0.5 bg-navy-700 text-slate-400 rounded-full">KPI: {rec.kpi_name}</span>}
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200">{rec.action}</h3>

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
                    <div className="bg-navy-900/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Owner</p>
                      <p className="text-xs font-medium text-slate-200 mt-0.5">{rec.owner}</p>
                    </div>
                    <div className="bg-navy-900/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Expected Impact</p>
                      <p className="text-xs font-medium text-green-400 mt-0.5">{rec.expected_impact}</p>
                    </div>
                    <div className="bg-navy-900/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Confidence</p>
                      <p className="text-xs font-medium text-slate-200 mt-0.5">{(rec.confidence * 100).toFixed(0)}%</p>
                    </div>
                    <div className="bg-navy-900/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Lever</p>
                      <p className="text-xs font-medium text-slate-200 mt-0.5">{rec.lever}</p>
                    </div>
                  </div>

                  {rec.monitoring_plan && (
                    <div className="flex items-center gap-2 mt-3 text-[10px] text-slate-500">
                      <Clock className="w-3 h-3" />
                      <span>Monitoring: {rec.monitoring_plan}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {recommendations.length === 0 && (
            <div className="text-center text-slate-400 py-20 text-sm">No recommendations at this time</div>
          )}
        </div>
      )}
    </div>
  );
}
