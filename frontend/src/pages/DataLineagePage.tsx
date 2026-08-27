import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import type { Lineage } from '../types';
import { GitBranch, Database, Calculator, Lightbulb, Target, ArrowDown } from 'lucide-react';

export default function DataLineagePage() {
  const [lineage, setLineage] = useState<Lineage | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLineage().then(setLineage).catch(console.error).finally(() => setLoading(false));
  }, []);

  const getIcon = (type: string) => {
    switch (type) {
      case 'source': return <Database size={14} />;
      case 'table': return <Database size={14} />;
      case 'transformation': return <Calculator size={14} />;
      case 'output': return <Lightbulb size={14} />;
      default: return <GitBranch size={14} />;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'source': return 'bg-primary/10 text-primary border-primary/20';
      case 'table': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'transformation': return 'bg-positive/10 text-positive border-positive/20';
      case 'output': return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      default: return 'bg-secondary text-muted-foreground border-border';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-foreground">Data Lineage</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Trace data from source to insight</p>
      </div>

      {loading ? (
        <div className="h-96 bg-secondary rounded-2xl animate-pulse" />
      ) : lineage ? (
        <div className="bg-card rounded-2xl border border-border p-6">
          <div className="flex flex-col items-center gap-2">
            {(['source', 'table', 'transformation', 'output'] as const).map((stage) => {
              const stageNodes = lineage.nodes.filter(n => n.type === stage);
              if (stageNodes.length === 0) return null;
              return (
                <div key={stage} className="flex flex-col items-center">
                  <div className="flex flex-wrap justify-center gap-3">
                    {stageNodes.map((node) => (
                      <div key={node.id} className={`px-4 py-3 rounded-xl border ${getColor(node.type)} min-w-[160px]`}>
                        <div className="flex items-center gap-2">
                          {getIcon(node.type)}
                          <span className="text-xs font-medium">{node.name}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  {stage !== 'output' && (
                    <div className="my-2">
                      <ArrowDown size={16} className="text-muted-foreground" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-6 pt-4 border-t border-border">
            <h3 className="text-xs font-medium text-muted-foreground mb-3">Data Flow Summary</h3>
            <div className="text-xs text-muted-foreground space-y-1">
              {lineage.edges.map((edge: { source: number; target: number }, i: number) => {
                const source = lineage.nodes.find(n => n.id === edge.source);
                const target = lineage.nodes.find(n => n.id === edge.target);
                return (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-foreground">{source?.name}</span>
                    <span className="text-muted-foreground">→</span>
                    <span className="text-foreground">{target?.name}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
