import React from 'react';
import { Shield } from 'lucide-react';

interface Props {
  score: number;
  level: string;
}

export default function ConfidenceGauge({ score, level }: Props) {
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? '#34c759' : score >= 50 ? '#ff9500' : '#ff3b30';

  return (
    <div className="bg-navy-700 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <Shield className="w-4 h-4 text-slate-500" />
        <h4 className="text-xs font-medium text-slate-400">CONFIDENCE</h4>
      </div>
      <div className="flex items-center gap-4">
        <div className="relative w-20 h-20">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#e8e8ed" strokeWidth="8" />
            <circle
              cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8"
              strokeDasharray={circumference} strokeDashoffset={offset}
              strokeLinecap="round" className="transition-all duration-700"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-bold text-slate-300" style={{ color }}>{score}%</span>
          </div>
        </div>
        <div>
          <p className={`text-sm font-medium ${
            level === 'high' ? 'text-success' : level === 'medium' ? 'text-warning' : 'text-danger'
          }`}>
            {level === 'high' ? 'High Confidence' : level === 'medium' ? 'Medium Confidence' : 'Low Confidence'}
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {score >= 80 ? 'Analysis is well-supported' : score >= 50 ? 'Some evidence gaps' : 'Insufficient evidence'}
          </p>
        </div>
      </div>
    </div>
  );
}
