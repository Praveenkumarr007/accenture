import React from 'react';
import {
  HelpCircle, Database, CalendarRange, Users, Shield,
  Lightbulb, Activity, MessageSquare, Info, Upload, AlertTriangle,
} from 'lucide-react';

interface FaqItem {
  icon: React.ComponentType<{ className?: string }>;
  q: string;
  a: string;
}

const faqs: FaqItem[] = [
  {
    icon: Database,
    q: 'What data does this dashboard use?',
    a: 'The dashboard analyzes three data sources: Sales (revenue, orders, products, regions), Marketing (campaign performance and conversion), and Inventory (stock levels). Data can be uploaded manually on the Data Upload page or comes from the pre-loaded demo dataset.',
  },
  {
    icon: CalendarRange,
    q: 'Why do some KPIs show "N/A" for change?',
    a: 'Change percentages compare the current period against a prior baseline period. If your uploaded data does not cover enough history for a prior period (e.g. only 7 days of data), the system honestly shows "N/A" instead of inventing a fake percentage.',
  },
  {
    icon: CalendarRange,
    q: 'How are analysis periods determined?',
    a: 'The analysis window adapts to your actual data span. About a week to two weeks of data uses the whole span as the current period. Longer datasets use rolling 14-day, 30-day, or 90-day windows, comparing against the preceding window of equal length.',
  },
  {
    icon: Users,
    q: 'What is the persona switcher (top-right)?',
    a: 'The persona selector changes the analysis lens: CEO for a full executive view, Sales Manager focused on sales KPIs, Marketing Manager focused on conversion and ROI. It frames the narrative, but does not change raw numbers. Actual data access is controlled by the role you log in with.',
  },
  {
    icon: Shield,
    q: 'How does role-based access work?',
    a: "The role you log in with decides which KPIs you may see. For example, a Sales Manager sees revenue, orders and average order value but not marketing ROI; a Supply Chain Manager sees only orders. Accessing a forbidden KPI returns a 403 error.",
  },
  {
    icon: Activity,
    q: 'What do the KPI cards and priorities mean?',
    a: 'Each KPI card shows the current value and its materiality priority. Priority reflects how significant the movement is: Critical, High, Medium or Low. A LOW or NONE priority means the change is not material enough to act on.',
  },
  {
    icon: Lightbulb,
    q: 'How are insights and drivers generated?',
    a: 'The engine runs a deterministic pipeline: it computes KPIs, detects anomalies and contradictions, decomposes changes into drivers (product, region, category), validates them with evidence across sources, and scores confidence before recommending actions.',
  },
  {
    icon: MessageSquare,
    q: 'How do I use the AI Assistant?',
    a: 'Open the AI Assistant and ask questions in plain language, e.g. "Why did revenue decline?" or "What should I do next?". It maps your question to the relevant KPI and answers with drivers, confidence and recommendations. You can also tap a suggested question to start.',
  },
  {
    icon: Upload,
    q: 'How do I upload my own data?',
    a: 'Go to Data Upload, select a CSV/Excel file, preview it, optionally map columns to sales/marketing/inventory types, and connect it. The dashboard then runs all analyses against your uploaded data.',
  },
  {
    icon: AlertTriangle,
    q: 'Why does the system sometimes abstain from a conclusion?',
    a: 'If confidence is too low or key data sources are missing, the system honestly states it cannot reach a definitive conclusion ("insufficient evidence") rather than guessing. Check the confidence score and missing data list on the insight.',
  },
  {
    icon: Info,
    q: 'Where do I find system/version details?',
    a: 'The Admin tab shows the application version, database backend, auth method and LLM status. It is only accessible by users with the Admin or CEO role.',
  },
];

export default function HelpPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-accent" /> Help & FAQ
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">How the dashboard works, its data, and its access rules</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {faqs.map((item) => (
          <div key={item.q} className="bg-navy-800 rounded-xl p-5 card-glow">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg gradient-accent flex items-center justify-center flex-shrink-0 mt-0.5">
                <item.icon className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-slate-300">{item.q}</h3>
                <p className="text-xs text-slate-400 leading-relaxed mt-1.5">{item.a}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}