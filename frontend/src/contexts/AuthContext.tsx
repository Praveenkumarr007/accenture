import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, setAuthToken } from '../lib/api';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  persona: string;
  setPersona: (p: string) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: async () => {},
  logout: () => {},
  loading: true,
  persona: 'CEO',
  setPersona: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [persona, setPersona] = useState('CEO');

  useEffect(() => {
    const savedToken = localStorage.getItem('bi_token');
    const savedUser = localStorage.getItem('bi_user');
    if (savedToken && savedUser) {
      setAuthToken(savedToken);
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setPersona(JSON.parse(savedUser).role_name === 'Marketing Manager' ? 'Marketing Manager' : 'CEO');
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result = await api.login(username, password);
    setAuthToken(result.access_token);
    setToken(result.access_token);
    setUser(result.user);
    localStorage.setItem('bi_token', result.access_token);
    localStorage.setItem('bi_user', JSON.stringify(result.user));
    if (result.user.role_name === 'Marketing Manager') {
      setPersona('Marketing Manager');
    } else {
      setPersona('CEO');
    }
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    setToken(null);
    setUser(null);
    localStorage.removeItem('bi_token');
    localStorage.removeItem('bi_user');
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, persona, setPersona }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
