import { useAuth } from '../../stores/AuthContext';
import { Menu, Bot, LogOut, User, Bell } from 'lucide-react';
import { useState } from 'react';

interface TopBarProps {
  onToggleSidebar: () => void;
  onToggleAssistant: () => void;
}

export default function TopBar({ onToggleSidebar, onToggleAssistant }: TopBarProps) {
  const { user, persona, setPersona, logout } = useAuth();
  const [showPersonaMenu, setShowPersonaMenu] = useState(false);

  const personas = ['CEO', 'Marketing Manager', 'Sales Manager', 'Admin'];

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <button onClick={onToggleSidebar} className="p-1.5 rounded-md hover:bg-accent text-muted-foreground lg:hidden">
          <Menu size={18} />
        </button>
        <div className="hidden sm:block">
          <span className="text-xs text-muted-foreground">Active Persona:</span>
          <span className="ml-2 text-xs font-semibold text-primary">{persona}</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative">
          <button
            onClick={() => setShowPersonaMenu(!showPersonaMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-secondary text-xs text-foreground hover:bg-accent transition-colors"
          >
            <User size={14} />
            <span>Switch Persona</span>
          </button>
          {showPersonaMenu && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-lg shadow-xl z-50">
              {personas.map((p) => (
                <button
                  key={p}
                  onClick={() => { setPersona(p); setShowPersonaMenu(false); }}
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-accent transition-colors ${
                    persona === p ? 'text-primary bg-primary/5' : 'text-foreground'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={onToggleAssistant}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-xs hover:bg-primary/20 transition-colors"
        >
          <Bot size={14} />
          <span className="hidden sm:inline">AI Assistant</span>
        </button>

        <button onClick={logout} className="p-1.5 rounded-md hover:bg-accent text-muted-foreground">
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}
