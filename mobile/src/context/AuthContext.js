import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { loadToken, saveToken, clearToken, auth, profile as profileApi, onTokenExpired } from '../api/client';
import logger from '../utils/logger';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);

  const clearSession = useCallback(() => {
    logger.info('Auth', 'Session cleared');
    setUser(null);
    setProfileData(null);
  }, []);

  useEffect(() => {
    // Register 401 handler so client.js can notify us
    onTokenExpired(clearSession);
  }, [clearSession]);

  useEffect(() => {
    (async () => {
      try {
        const token = await loadToken();
        if (token) {
          const data = await profileApi.me();
          setUser({ username: data.username, email: data.email });
          setProfileData(data);
        }
      } catch (e) {
        logger.warn('Auth', 'Initial token validation failed, clearing', e);
        await clearToken();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (username, password) => {
    const data = await auth.login(username, password);
    await saveToken(data.token);
    setUser({ username: data.username, id: data.user_id });
    setProfileData(data.profile);
    return data;
  };

  const register = async (regData) => {
    const data = await auth.register(regData);
    await saveToken(data.token);
    setUser({ username: data.username, id: data.user_id });
    setProfileData(data.profile);
    return data;
  };

  const refreshAfterPhoneLogin = (data) => {
    setUser({ username: data.username, id: data.user_id });
    setProfileData(data.profile);
  };

  const logout = async () => {
    try { await auth.logout(); } catch (e) {
      logger.warn('Auth', 'Logout API call failed (best-effort)', e);
    }
    await clearToken();
    setUser(null);
    setProfileData(null);
  };

  const refreshProfile = async () => {
    const data = await profileApi.me();
    setProfileData(data);
  };

  return (
    <AuthContext.Provider value={{ user, profileData, loading, login, register, logout, refreshProfile, refreshAfterPhoneLogin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
