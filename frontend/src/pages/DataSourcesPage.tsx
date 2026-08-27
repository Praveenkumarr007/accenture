import React, { useEffect, useState } from 'react';
import { Database, CheckCircle, AlertCircle, Clock, HardDrive } from 'lucide-react';
import { api } from '../lib/api';
import { timeAgo } from '../lib/utils';
import type { DataSourceInfo } from '../types';

export default function DataSourcesPage() {
  const [sources, setSources] = useState<DataSourceInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getDataSources();
      setSources(res.data_sources);
    } catch {} finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Data Sources</h1>
        <p className="text-sm text-slate-400 mt-0.5">Connected data sources and their freshness status</p>
      </div>

      {loading ? (
        <div className="text-center text-slate-400 py-20 text-sm">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sources.map(source => (
            <div key={source.id} className="bg-navy-800 rounded-xl p-5 card-glow">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  source.status === 'healthy' ? 'bg-green-500/20' : 'bg-red-500/20'
                }`}>
                  <Database className={`w-5 h-5 ${source.status === 'healthy' ? 'text-green-400' : 'text-red-400'}`} />
                </div>
                <div>
                  <h3 className="font-semibold text-sm">{source.name}</h3>
                  <p className="text-[10px] text-slate-500">{source.source_type}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Status</span>
                  <span className={`flex items-center gap-1.5 text-xs font-medium ${
                    source.status === 'healthy' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {source.status === 'healthy' ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                    {source.status}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Last Updated</span>
                  <span className="text-xs text-slate-300 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {source.last_updated ? timeAgo(source.last_updated) : 'Unknown'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Refresh Frequency</span>
                  <span className="text-xs text-slate-300">{source.refresh_frequency}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Rows</span>
                  <span className="text-xs text-slate-300">{source.row_count.toLocaleString()}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Quality Score</span>
                  <span className={`text-xs font-medium ${
                    source.data_quality_score >= 0.9 ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    {(source.data_quality_score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Coverage</span>
                  <span className="text-xs text-slate-300">{source.coverage_days} days</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-700/50">
                <p className="text-[10px] text-slate-500">{source.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-navy-800 rounded-xl p-5 card-glow">
        <h3 className="font-semibold text-sm mb-3">Data Freshness Comparison</h3>
        <div className="space-y-3">
          {sources.map(source => (
            <div key={source.id} className="flex items-center gap-4">
              <span className="text-xs text-slate-300 w-36">{source.name}</span>
              <div className="flex-1 h-3 bg-navy-900 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${(source.data_quality_score * 100)}%`,
                    backgroundColor: source.data_quality_score >= 0.9 ? '#22c55e' : '#f59e0b',
                  }}
                />
              </div>
              <span className="text-xs text-slate-400 w-20 text-right">{source.refresh_frequency}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
