/**
 * Environment configuration.
 *
 * For local development, create a .env.local file (git-ignored) to override:
 *   EXPO_PUBLIC_API_URL=http://localhost:8000/api
 *
 * For production builds, set EXPO_PUBLIC_API_URL in your EAS build secrets
 * or app.config.js extra field.
 */
import { Platform } from 'react-native';
import Constants from 'expo-constants';

// Read from Expo public env vars (set via .env or EAS secrets)
const EXPO_API_URL = Constants.expoConfig?.extra?.apiUrl
  || (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL)
  || null;

const ENV = {
  // API base URLs — production must use HTTPS
  API_URL_PRODUCTION: 'https://api.covoitafrica.com/api',
  API_URL_WEB_DEV: 'http://localhost:8000/api',
  API_URL_NATIVE_DEV: 'http://172.26.144.1:8000/api',

  // Network (African 2G/3G resilience)
  REQUEST_TIMEOUT_MS: 30 * 1000, // 30s timeout for slow networks
  MAX_RETRIES: 2, // retry failed requests up to 2 times
  RETRY_DELAY_MS: 1000, // 1s initial delay, doubles each retry

  // Cache (24h for intermittent connectivity)
  CACHE_TTL_MS: 24 * 60 * 60 * 1000, // 24 hours

  // Auth
  TOKEN_REFRESH_MARGIN_MS: 5 * 60 * 1000, // refresh 5 min before expiry
};

/**
 * Returns the API base URL for the current platform and environment.
 * Priority: EXPO_PUBLIC_API_URL env var > __DEV__ dev URLs > production URL
 */
export function getApiUrl() {
  // 1. Explicit env var override (from .env or EAS secrets)
  if (EXPO_API_URL) return EXPO_API_URL;

  // 2. Development mode — use local URLs
  if (__DEV__) {
    return Platform.OS === 'web' ? ENV.API_URL_WEB_DEV : ENV.API_URL_NATIVE_DEV;
  }

  // 3. Production — always HTTPS
  return ENV.API_URL_PRODUCTION;
}

export default ENV;
