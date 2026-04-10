import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Platform } from 'react-native';
import logger from '../utils/logger';
import fr from './fr';
import en from './en';

const translations = { fr, en };

const I18nContext = createContext(null);

function getStoredLang() {
  if (Platform.OS === 'web') {
    return localStorage.getItem('app_language') || 'fr';
  }
  return 'fr';
}

function storeLang(lang) {
  if (Platform.OS === 'web') {
    localStorage.setItem('app_language', lang);
  }
}

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState('fr');

  useEffect(() => {
    const loadLang = async () => {
      if (Platform.OS !== 'web') {
        try {
          const SecureStore = require('expo-secure-store');
          const saved = await SecureStore.getItemAsync('app_language');
          if (saved && translations[saved]) setLangState(saved);
        } catch (e) {
          logger.warn('I18n', 'Failed to load saved language', e);
        }
      } else {
        const saved = getStoredLang();
        if (saved && translations[saved]) setLangState(saved);
      }
    };
    loadLang();
  }, []);

  const setLang = useCallback(async (newLang) => {
    if (!translations[newLang]) return;
    setLangState(newLang);
    if (Platform.OS === 'web') {
      storeLang(newLang);
    } else {
      try {
        const SecureStore = require('expo-secure-store');
        await SecureStore.setItemAsync('app_language', newLang);
      } catch (e) {
        logger.warn('I18n', 'Failed to persist language choice', e);
      }
    }
  }, []);

  const t = useCallback((key) => {
    return translations[lang]?.[key] || translations.fr[key] || key;
  }, [lang]);

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
