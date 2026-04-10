import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from './logger';

const CACHE_PREFIX = '@covoit_cache_';
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

export async function getCached(key) {
  try {
    const raw = await AsyncStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const { data, timestamp } = JSON.parse(raw);
    if (Date.now() - timestamp > CACHE_TTL) {
      await AsyncStorage.removeItem(CACHE_PREFIX + key);
      return null;
    }
    return data;
  } catch (e) {
    logger.warn('Cache', `getCached(${key}) failed`, e);
    return null;
  }
}

export async function setCache(key, data) {
  try {
    await AsyncStorage.setItem(
      CACHE_PREFIX + key,
      JSON.stringify({ data, timestamp: Date.now() })
    );
  } catch (e) {
    logger.warn('Cache', `setCache(${key}) failed`, e);
  }
}

export async function clearCache() {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const cacheKeys = keys.filter(k => k.startsWith(CACHE_PREFIX));
    if (cacheKeys.length > 0) {
      await AsyncStorage.multiRemove(cacheKeys);
    }
  } catch (e) {
    logger.warn('Cache', 'clearCache failed', e);
  }
}

/**
 * Fetch with offline fallback: tries the API call, caches success,
 * returns cached data on failure.
 */
export async function fetchWithCache(cacheKey, apiFn) {
  try {
    const data = await apiFn();
    await setCache(cacheKey, data);
    return { data, fromCache: false };
  } catch (err) {
    const cached = await getCached(cacheKey);
    if (cached) {
      return { data: cached, fromCache: true };
    }
    throw err;
  }
}
