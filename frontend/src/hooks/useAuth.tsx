import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { getCurrentUser, setCurrentUser, getAuthToken, setAuthToken } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  switchPersona: (role: string) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
  switchPersona: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getCurrentUser());
  const isAuthenticated = !!user && !!getAuthToken();

  const login = (userData: User, token: string) => {
    setAuthToken(token);
    setCurrentUser(userData);
    setUser(userData);
  };

  const logout = () => {
    setAuthToken(null);
    setCurrentUser(null);
    setUser(null);
  };

  const switchPersona = (role: string) => {
    if (!user) return;
    const switched = { ...user, role_name: role };
    setCurrentUser(switched);
    setUser(switched);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout, switchPersona }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
