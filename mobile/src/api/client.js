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
    // Backend authenticates with SimpleJWT (Bearer), not DRF TokenAuth.
    headers['Authorization'] = `Bearer ${_token}`;
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
  me: () => request('GET', '/profiles/me/'),
  update: (data) => request('PATCH', '/profiles/me/', data),
  public: (username) => request('GET', `/profiles/?search=${encodeURIComponent(username)}`, null, true),
};

// ─── Voyages ──────────────────────────────────────────────
export const voyages = {
  search: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request('GET', `/voyages/search/?${qs}`, null, true);
  },
  mine: () => request('GET', '/voyages/mine/'),
  create: (data) => request('POST', '/voyages/', data),
  update: (id, data) => request('PATCH', `/voyages/${id}/`, data),
  delete: (id) => request('DELETE', `/voyages/${id}/`),
  markTermine: (id) => request('POST', `/voyages/${id}/termine/`),
};

// ─── Demandes ─────────────────────────────────────────────
export const demandes = {
  mine: () => request('GET', '/demandes/'), // list is already scoped to the user
  create: (data) => request('POST', '/demandes/', data),
  delete: (id) => request('DELETE', `/demandes/${id}/`),
};

// ─── Matches (correspondances) ─────────────────────────────
export const matches = {
  mine: () => request('GET', '/correspondances/'),
  validate: (id) => request('POST', `/correspondances/${id}/validate/`),
  refuse: (id) => request('POST', `/correspondances/${id}/refuse/`),
};

// ─── Reviews (avis) ────────────────────────────────────────
export const reviews = {
  mine: () => request('GET', '/avis/'),
  create: (data) => request('POST', '/avis/', data),
};

// ─── Notifications ────────────────────────────────────────
export const notifications = {
  list: () => request('GET', '/notifications/'),
  markRead: (id) => request('POST', `/notifications/${id}/mark_read/`),
  markAllRead: () => request('POST', '/notifications/mark_all_read/'),
};

// ─── Messaging ────────────────────────────────────────────
export const messaging = {
  conversation: (correspondanceId) => request('GET', `/correspondances/${correspondanceId}/messages/`),
  send: (correspondanceId, content) =>
    request('POST', `/correspondances/${correspondanceId}/messages/`, { content }),
};

// ─── Dashboard ────────────────────────────────────────────
export const dashboard = {
  stats: () => request('GET', '/dashboard/'),
};

// ─── Payments (Mobile-Money escrow on a match) ─────────────
export const payments = {
  // Passenger pays the fare into escrow for a validated match.
  create: (data) =>
    request('POST', `/correspondances/${data.correspondance_id}/pay/`, {
      phone: data.phone_number,
      provider: data.provider,
    }),
  // Passenger cancels before pickup → refund.
  refund: (correspondanceId) => request('POST', `/correspondances/${correspondanceId}/refund/`),
};

// ─── Wallet (Driver Commission) ────────────────────────────
export const wallet = {
  // Backend returns balance + transactions together at /wallet/.
  balance: () => request('GET', '/wallet/'),
  transactions: () => request('GET', '/wallet/'),
};

// ─── Safety (SOS / live-trip-share) ────────────────────────
export const safety = {
  share: (correspondanceId) => request('POST', `/correspondances/${correspondanceId}/share/`),
  sos: (correspondanceId) => request('POST', `/correspondances/${correspondanceId}/sos/`),
};

// ─── Saved-route alerts ────────────────────────────────────
export const routeAlerts = {
  list: () => request('GET', '/route-alerts/'),
  create: (data) => request('POST', '/route-alerts/', data),
  delete: (id) => request('DELETE', `/route-alerts/${id}/`),
};

// ─── Recurring trips (weekly commutes) ─────────────────────
export const recurringTrips = {
  list: () => request('GET', '/recurring-trips/'),
  create: (data) => request('POST', '/recurring-trips/', data),
  delete: (id) => request('DELETE', `/recurring-trips/${id}/`),
};

