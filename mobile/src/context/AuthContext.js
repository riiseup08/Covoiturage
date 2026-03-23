import React, { createContext, useContext, useState, useEffect } from 'react';
import { loadToken, saveToken, clearToken, auth, profile as profileApi } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const token = await loadToken();
        if (token) {
          const data = await profileApi.me();
          setUser({ username: data.username, email: data.email });
          setProfileData(data);
        }
      } catch {
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

  const logout = async () => {
    try { await auth.logout(); } catch { /* ignore */ }
    await clearToken();
    setUser(null);
    setProfileData(null);
  };

  const refreshProfile = async () => {
    const data = await profileApi.me();
    setProfileData(data);
  };

  return (
    <AuthContext.Provider value={{ user, profileData, loading, login, register, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
