import { Platform } from 'react-native';

let SecureStore = null;
if (Platform.OS !== 'web') {
  SecureStore = require('expo-secure-store');
}

// Change this to your Django server URL
const BASE_URL = Platform.OS === 'web'
  ? 'http://localhost:8000/api'
  : 'http://172.26.144.1:8000/api';

let _token = null;

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
  const headers = { 'Content-Type': 'application/json' };
  if (!isPublic && _token) {
    headers['Authorization'] = `Token ${_token}`;
  }
  const config = { method, headers };
  if (body) {
    config.body = JSON.stringify(body);
  }
  const res = await fetch(`${BASE_URL}${path}`, config);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error || data.detail || JSON.stringify(data);
    throw new Error(msg);
  }
  return data;
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
