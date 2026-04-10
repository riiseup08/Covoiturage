/**
 * Environment configuration.
 *
 * In production, use react-native-dotenv or expo-constants to load from .env.
 * This module centralizes all environment-dependent values.
 */
import { Platform } from 'react-native';

const ENV = {
  // API base URLs
  API_URL_WEB: 'http://localhost:8000/api',
  API_URL_NATIVE: 'http://172.26.144.1:8000/api',

  // Cache
  CACHE_TTL_MS: 30 * 60 * 1000, // 30 minutes

  // Auth
  TOKEN_REFRESH_MARGIN_MS: 5 * 60 * 1000, // refresh 5 min before expiry
};

/**
 * Returns the API base URL for the current platform.
 */
export function getApiUrl() {
  return Platform.OS === 'web' ? ENV.API_URL_WEB : ENV.API_URL_NATIVE;
}

export default ENV;
