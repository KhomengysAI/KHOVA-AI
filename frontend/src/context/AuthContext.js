import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { authMe, exchangeSession, devLogin as devLoginApi, logoutApi } from '@/lib/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUserState] = useState(null);
  const userRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const pendingAction = useRef(null);

  const applyUser = useCallback((u) => { userRef.current = u; setUserState(u); }, []);

  const runPending = useCallback(() => {
    if (pendingAction.current) {
      const a = pendingAction.current;
      pendingAction.current = null;
      setTimeout(a, 60);
    }
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      const u = await authMe();
      applyUser(u);
      return u;
    } catch (e) {
      applyUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, [applyUser]);

  useEffect(() => {
    // CRITICAL: If returning from OAuth callback, skip the /me check; AuthCallback handles it.
    if (window.location.hash?.includes('session_id=')) { setLoading(false); return; }
    checkAuth();
  }, [checkAuth]);

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const googleLogin = useCallback(() => {
    localStorage.setItem('khova_return_to', window.location.pathname);
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  }, []);

  const processSession = useCallback(async (session_id) => {
    const data = await exchangeSession(session_id);
    applyUser(data.user);
    return data.user;
  }, [applyUser]);

  const devLogin = useCallback(async (email, name) => {
    const data = await devLoginApi(email || 'tester@khova.ai', name || 'Tester');
    applyUser(data.user);
    setShowLogin(false);
    runPending();
    return data.user;
  }, [applyUser, runPending]);

  const logout = useCallback(async () => {
    try { await logoutApi(); } catch (e) {}
    applyUser(null);
  }, [applyUser]);

  // ensureAuth: stable (reads userRef so stored pending actions always see current auth).
  const ensureAuth = useCallback((action) => {
    if (userRef.current) return true;
    if (action) pendingAction.current = action;
    setShowLogin(true);
    return false;
  }, []);

  const onLoginSuccess = useCallback((u) => {
    applyUser(u);
    setShowLogin(false);
    runPending();
  }, [applyUser, runPending]);

  return (
    <AuthContext.Provider value={{ user, loading, showLogin, setShowLogin, googleLogin, processSession, devLogin, logout, ensureAuth, checkAuth, onLoginSuccess }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
