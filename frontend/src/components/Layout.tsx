import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard, Activity, Lightbulb, GitBranch, Target,
  Database, MessageSquare, FileText, Settings, Bot, LogOut,
  ChevronLeft, ChevronRight, User, Bell
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/kpis', label: 'KPI Monitor', icon: Activity },
  { path: '/insights', label: 'Insights', icon: Lightbulb },
  { path: '/drivers', label: 'Drivers', icon: GitBranch },
  { path: '/recommendations', label: 'Recommendations', icon: Target },
  { path: '/data-sources', label: 'Data Sources', icon: Database },
  { path: '/lineage', label: 'Data Lineage', icon: GitBranch },
  { path: '/feedback', label: 'Feedback', icon: MessageSquare },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/admin', label: 'Admin', icon: Settings },
  { path: '/assistant', label: 'AI Assistant', icon: Bot },
];

export default function Layout() {
  const { user, logout, persona, setPersona } = useAuth();
  const navigate = useNavigate();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-navy-900">
      <aside
        className={`${
          sidebarCollapsed ? 'w-16' : 'w-60'
        } bg-navy-800 border-r border-slate-700/50 flex flex-col transition-all duration-300`}
      >
        <div className="p-4 border-b border-slate-700/50">
          {!sidebarCollapsed ? (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">BI</span>
              </div>
              <div>
                <div className="text-sm font-semibold text-white">BusinessIntelligence</div>
                <div className="text-[10px] text-slate-400">.AI Platform</div>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto">
              <span className="text-white font-bold text-sm">BI</span>
            </div>
          )}
        </div>

        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
                } ${sidebarCollapsed ? 'justify-center' : ''}`
              }
            >
              <item.icon size={18} />
              {!sidebarCollapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="p-2 border-t border-slate-700/50">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center justify-center p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/30"
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 bg-navy-800/80 border-b border-slate-700/50 flex items-center justify-between px-6 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-medium text-slate-300">ShopSmart Analytics</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Persona:</span>
              <select
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                className="bg-navy-700 border border-slate-600 rounded-md px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="CEO">CEO</option>
                <option value="Marketing Manager">Marketing Manager</option>
              </select>
            </div>

            <button className="relative p-2 text-slate-400 hover:text-slate-200">
              <Bell size={16} />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            <div className="flex items-center gap-2 pl-4 border-l border-slate-700">
              <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center">
                <User size={14} className="text-slate-300" />
              </div>
              <div className="text-xs">
                <div className="text-slate-200 font-medium">{user?.full_name}</div>
                <div className="text-slate-500">{user?.role_name}</div>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-red-400 transition-colors"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
