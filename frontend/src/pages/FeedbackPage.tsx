import React, { useEffect, useState } from 'react';
import { ThumbsUp, ThumbsDown, MessageSquare, BarChart3 } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import type { FeedbackDashboard } from '../types';

export default function FeedbackPage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<FeedbackDashboard | null>(null);
  const [insightId, setInsightId] = useState('revenue');
  const [feedbackType, setFeedbackType] = useState('');
  const [correction, setCorrection] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.getFeedbackDashboard();
      setDashboard(res);
    } catch {} finally { setLoading(false); }
  };

  const submitFeedback = async (rating: 'correct' | 'incorrect') => {
    try {
      await api.submitFeedback({
        insight_id: insightId.length > 0 ? 1 : 0,
        rating,
        feedback_type: feedbackType || undefined,
        correction: correction || undefined,
      });
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
      loadDashboard();
    } catch {}
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Feedback</h1>
        <p className="text-sm text-slate-400 mt-0.5">Provide feedback on insights and recommendations</p>
      </div>

      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-accent" />
              <span className="text-xs text-slate-400">Total Feedback</span>
            </div>
            <p className="text-2xl font-bold">{dashboard.total_feedback}</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <ThumbsUp className="w-4 h-4 text-green-400" />
              <span className="text-xs text-slate-400">Positive</span>
            </div>
            <p className="text-2xl font-bold text-green-400">{dashboard.positive_count}</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <ThumbsDown className="w-4 h-4 text-red-400" />
              <span className="text-xs text-slate-400">Negative</span>
            </div>
            <p className="text-2xl font-bold text-red-400">{dashboard.negative_count}</p>
          </div>
          <div className="bg-navy-800 rounded-xl p-4 card-glow">
            <div className="flex items-center gap-2 mb-2">
              <MessageSquare className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-slate-400">Positive Rate</span>
            </div>
            <p className="text-2xl font-bold">{dashboard.positive_rate}%</p>
          </div>
        </div>
      )}

      <div className="bg-navy-800 rounded-xl p-5 card-glow">
        <h3 className="font-semibold text-sm mb-4">Submit Feedback</h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">KPI Insight</label>
            <select
              value={insightId}
              onChange={e => setInsightId(e.target.value)}
              className="w-full bg-navy-700 border border-slate-600 rounded-lg px-4 py-2 text-sm text-slate-300 focus:outline-none focus:border-accent"
            >
              <option value="revenue">Revenue</option>
              <option value="orders">Orders</option>
              <option value="aov">Average Order Value</option>
              <option value="conversion_rate">Conversion Rate</option>
              <option value="marketing_roi">Marketing ROI</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Feedback Type (optional)</label>
            <select
              value={feedbackType}
              onChange={e => setFeedbackType(e.target.value)}
              className="w-full bg-navy-700 border border-slate-600 rounded-lg px-4 py-2 text-sm text-slate-300 focus:outline-none focus:border-accent"
            >
              <option value="">Select type...</option>
              <option value="incorrect_driver">Incorrect driver</option>
              <option value="incorrect_recommendation">Incorrect recommendation</option>
              <option value="insufficient_evidence">Insufficient evidence</option>
              <option value="wrong_kpi">Wrong KPI</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Correction / Notes (optional)</label>
            <textarea
              value={correction}
              onChange={e => setCorrection(e.target.value)}
              className="w-full bg-navy-700 border border-slate-600 rounded-lg px-4 py-2 text-sm text-slate-300 focus:outline-none focus:border-accent h-20 resize-none"
              placeholder="Describe the issue or correction..."
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => submitFeedback('correct')}
              className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg text-sm hover:bg-green-500/30 transition"
            >
              <ThumbsUp className="w-4 h-4" /> Correct
            </button>
            <button
              onClick={() => submitFeedback('incorrect')}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg text-sm hover:bg-red-500/30 transition"
            >
              <ThumbsDown className="w-4 h-4" /> Incorrect
            </button>
          </div>
          {submitted && (
            <p className="text-xs text-green-400">Feedback submitted successfully!</p>
          )}
        </div>
      </div>

      <div className="bg-navy-800 rounded-xl p-5 card-glow">
        <h3 className="font-semibold text-sm mb-3">Learning Loop</h3>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-1 bg-accent/20 text-accent rounded-lg">Insight</span>
          <span>→</span>
          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-lg">User Feedback</span>
          <span>→</span>
          <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded-lg">Evaluation</span>
          <span>→</span>
          <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-lg">Rule Update</span>
          <span>→</span>
          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-lg">Improved Insights</span>
        </div>
      </div>
    </div>
  );
}
