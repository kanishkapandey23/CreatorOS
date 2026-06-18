'use client';

/**
 * AuthProvider — placeholder authentication context.
 *
 * Designed so that swapping in Supabase Auth later requires changing only
 * `authService` implementation. Components should ONLY interact with
 * the `useAuth()` hook — never call services directly.
 */

import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { authService } from '@/services/auth.service';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading'); // 'loading' | 'authenticated' | 'unauthenticated'

  useEffect(() => {
    let cancelled = false;
    authService
      .getSession()
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        setStatus(u ? 'authenticated' : 'unauthenticated');
      })
      .catch(() => setStatus('unauthenticated'));
    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (payload) => {
    const u = await authService.signIn(payload);
    setUser(u);
    setStatus('authenticated');
    return u;
  }, []);

  const signInWith = useCallback(async (provider) => {
    const u = await authService.signInWithOAuth(provider);
    setUser(u);
    setStatus('authenticated');
    return u;
  }, []);

  const signUp = useCallback(async (payload) => {
    const u = await authService.signUp(payload);
    setUser(u);
    setStatus('authenticated');
    return u;
  }, []);

  const signOut = useCallback(async () => {
    await authService.signOut();
    setUser(null);
    setStatus('unauthenticated');
  }, []);

  const value = useMemo(
    () => ({ user, status, signIn, signInWith, signUp, signOut }),
    [user, status, signIn, signInWith, signUp, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
