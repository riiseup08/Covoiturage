import { Platform } from 'react-native';
import { getApiUrl } from '../config/env';
import ENV from '../config/env';
import logger from '../utils/logger';

let SecureStore = null;
if (Platform.OS !== 'web') {
  SecureStore = require('expo-secure-store');
}

const BASE_URL = getApiUrl();

let _token = null;
let _onTokenExpired = null;

/**
 * Register a callback invoked when a 401 is detected.
 * AuthContext uses this to clear state and redirect to login.
 */
export function onTokenExpired(cb) {
  _onTokenExpired = cb;
}

export async function loadToken() {
  if (Platform.OS === 'web') {
    _token = localStorage.getItem('auth_token');
  } else {
    _token = await SecureStore.getItemAsync('auth_token');
  }
  return _token;
}

export async function saveToken(token) {
  _token = token;
  if (Platform.OS === 'web') {
    localStorage.setItem('auth_token', token);
  } else {
    await SecureStore.setItemAsync('auth_token', token);
  }
}

export async function clearToken() {
  _token = null;
  if (Platform.OS === 'web') {
    localStorage.removeItem('auth_token');
  } else {
    await SecureStore.deleteItemAsync('auth_token');
  }
}

export function getToken() {
  return _token;
}

async function request(method, path, body = null, isPublic = false) {
  const headers = { 'Content-Type': 'application/json', 'Accept-Encoding': 'gzip' };
  if (!isPublic && _token) {
    headers['Authorization'] = `Token ${_token}`;
  }
  const config = { method, headers };
  if (body) {
    config.body = JSON.stringify(body);
  }
  const url = `${BASE_URL}${path}`;

  let lastError;
  for (let attempt = 0; attempt <= ENV.MAX_RETRIES; attempt++) {
    if (attempt > 0) {
      const delay = ENV.RETRY_DELAY_MS * Math.pow(2, attempt - 1);
      logger.info('API', `Retry ${attempt}/${ENV.MAX_RETRIES} for ${method} ${path} after ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
    try {
      logger.debug('API', `${method} ${path}`);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), ENV.REQUEST_TIMEOUT_MS);
      const res = await fetch(url, { ...config, signal: controller.signal });
      clearTimeout(timeout);

      // Token expired — clear and notify
      if (res.status === 401 && !isPublic) {
        logger.warn('API', 'Token expired (401), clearing session');
        await clearToken();
        if (_onTokenExpired) _onTokenExpired();
        throw new Error('Session expired');
      }

      if (res.status === 204) return null;
      const data = await res.json();
      if (!res.ok) {
        const msg = data.error || data.detail || JSON.stringify(data);
        logger.error('API', `${method} ${path} failed (${res.status})`, msg);
        throw new Error(msg);
      }
      return data;
    } catch (e) {
      lastError = e;
      // Don't retry auth errors or client errors
      if (e.message === 'Session expired' || (e.message && !e.message.includes('aborted') && !e.message.includes('network') && !e.message.includes('Failed to fetch'))) {
        throw e;
      }
    }
  }
  logger.error('API', `${method} ${path} failed after ${ENV.MAX_RETRIES + 1} attempts`, lastError?.message);
  throw lastError;
}

// ─── Auth ─────────────────────────────────────────────────
export const auth = {
  login: (username, password) => request('POST', '/auth/login/', { username, password }, true),
  register: (data) => request('POST', '/auth/register/', data, true),
  logout: () => request('POST', '/auth/logout/'),
  phoneRequestOtp: (phone) => request('POST', '/auth/phone/request-otp/', { phone }, true),
  phoneVerifyOtp: (phone, code) => request('POST', '/auth/phone/verify-otp/', { phone, code }, true),
  phoneRegister: (data) => request('POST', '/auth/phone/register/', data, true),
};

// ─── Profile ──────────────────────────────────────────────
export const profile = {
  me: () => request('GET', '/profile/'),
  update: (data) => request('PATCH', '/profile/update/', data),
  public: (username) => request('GET', `/profile/${username}/`),
};

// ─── Voyages ──────────────────────────────────────────────
export const voyages = {
  search: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request('GET', `/voyages/search/?${qs}`, null, true);
  },
  mine: () => request('GET', '/voyages/mine/'),
  create: (data) => request('POST', '/voyages/create/', data),
  update: (id, data) => request('PATCH', `/voyages/${id}/update/`, data),
  delete: (id) => request('DELETE', `/voyages/${id}/delete/`),
  markTermine: (id) => request('POST', `/voyages/${id}/termine/`),
};

// ─── Demandes ─────────────────────────────────────────────
export const demandes = {
  mine: () => request('GET', '/demandes/mine/'),
  create: (data) => request('POST', '/demandes/create/', data),
  delete: (id) => request('DELETE', `/demandes/${id}/delete/`),
};

// ─── Matches ──────────────────────────────────────────────
export const matches = {
  mine: () => request('GET', '/matches/'),
  validate: (id) => request('POST', `/matches/${id}/validate/`),
  refuse: (id) => request('POST', `/matches/${id}/refuse/`),
};

// ─── Reviews ──────────────────────────────────────────────
export const reviews = {
  mine: () => request('GET', '/reviews/'),
  create: (data) => request('POST', '/reviews/create/', data),
};

// ─── Notifications ────────────────────────────────────────
export const notifications = {
  list: () => request('GET', '/notifications/'),
  markRead: (id) => request('POST', `/notifications/${id}/read/`),
  markAllRead: () => request('POST', '/notifications/read-all/'),
};

// ─── Messaging ────────────────────────────────────────────
export const messaging = {
  conversation: (id) => request('GET', `/conversation/${id}/`),
  send: (id, content) => request('POST', `/conversation/${id}/send/`, { content }),
};

// ─── Dashboard ────────────────────────────────────────────
export const dashboard = {
  stats: () => request('GET', '/dashboard/'),
};

// ─── Payments ─────────────────────────────────────────────
export const payments = {
  mine: () => request('GET', '/payments/'),
  create: (data) => request('POST', '/payments/create/', data),
  confirm: (id) => request('POST', `/payments/${id}/confirm/`),
};

// ─── Wallet (Driver Commission) ────────────────────────────
export const wallet = {
  balance: () => request('GET', '/wallet/balance/'),
  requestTopup: (data) => request('POST', '/wallet/topup/request/', data),
  confirmTopup: (id) => request('POST', `/wallet/topup/${id}/confirm/`),
  transactions: () => request('GET', '/wallet/transactions/'),
};

