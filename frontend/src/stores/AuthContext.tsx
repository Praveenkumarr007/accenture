import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../services/api';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  persona: string;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setPersona: (persona: string) => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [persona, setPersona] = useState<string>('CEO');

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setUser(parsed);
        setPersona(parsed.persona || parsed.role || 'CEO');
      } catch { /* ignore */ }
    }
  }, []);

  const login = async (email: string, password: string) => {
    const result = await api.auth.login(email, password);
    localStorage.setItem('token', result.access_token);
    localStorage.setItem('user', JSON.stringify(result.user));
    setUser(result.user);
    setPersona(result.user.persona || result.user.role || 'CEO');
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setPersona('CEO');
  };

  return (
    <AuthContext.Provider value={{ user, persona, login, logout, setPersona, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
