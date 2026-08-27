import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Activity, Lightbulb, GitBranch, Target,
  Database, MessageSquare, FileText, Settings, Bot, LogOut,
  ChevronLeft, ChevronRight, Zap, Upload
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/kpis', label: 'KPI Monitor', icon: Activity },
  { path: '/insights', label: 'Insights', icon: Lightbulb },
  { path: '/drivers', label: 'Drivers', icon: GitBranch },
  { path: '/recommendations', label: 'Recommendations', icon: Target },
  { path: '/datasources', label: 'Data Sources', icon: Database },
  { path: '/upload', label: 'Data Upload', icon: Upload },
  { path: '/feedback', label: 'Feedback', icon: MessageSquare },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/assistant', label: 'AI Assistant', icon: Bot },
  { path: '/admin', label: 'Admin', icon: Settings },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();

  return (
    <aside className={`${collapsed ? 'w-16' : 'w-60'} h-screen bg-navy-800 border-r border-slate-700/50 flex flex-col transition-all duration-300 flex-shrink-0`}>
      <div className="flex items-center gap-2 px-4 py-4 border-b border-slate-700/50">
        <div className="w-8 h-8 rounded-lg gradient-accent flex items-center justify-center flex-shrink-0">
          <Zap className="w-4 h-4" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <p className="text-sm font-bold tracking-tight">BI.AI</p>
            <p className="text-[10px] text-slate-500">KPI Intelligence</p>
          </div>
        )}
        <button onClick={() => setCollapsed(!collapsed)} className="ml-auto text-slate-500 hover:text-white transition">
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                isActive
                  ? 'bg-accent/15 text-accent-light font-medium'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              } ${collapsed ? 'justify-center' : ''}`
            }
          >
            <item.icon className="w-4 h-4 flex-shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-slate-700/50">
        {user && !collapsed && (
          <div className="mb-2 px-2">
            <p className="text-xs font-medium text-slate-300 truncate">{user.full_name}</p>
            <p className="text-[10px] text-slate-500">{user.role_name}</p>
          </div>
        )}
        <button
          onClick={logout}
          className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition ${collapsed ? 'justify-center' : ''}`}
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
