/**
 * Tests for mobile/src/utils/offline.js
 *
 * Run: npx jest src/__tests__/offline.test.js
 */

global.__DEV__ = true;

// Mock AsyncStorage
const store = {};
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn((key) => Promise.resolve(store[key] || null)),
  setItem: jest.fn((key, val) => { store[key] = val; return Promise.resolve(); }),
  removeItem: jest.fn((key) => { delete store[key]; return Promise.resolve(); }),
  getAllKeys: jest.fn(() => Promise.resolve(Object.keys(store))),
  multiRemove: jest.fn((keys) => { keys.forEach(k => delete store[k]); return Promise.resolve(); }),
}));

const { getCached, setCache, clearCache, fetchWithCache } = require('../utils/offline');

beforeEach(() => {
  Object.keys(store).forEach(k => delete store[k]);
  jest.clearAllMocks();
});

describe('setCache / getCached', () => {
  it('stores and retrieves data', async () => {
    await setCache('test_key', { hello: 'world' });
    const result = await getCached('test_key');
    expect(result).toEqual({ hello: 'world' });
  });

  it('returns null for missing keys', async () => {
    const result = await getCached('nonexistent');
    expect(result).toBeNull();
  });

  it('returns null for expired data', async () => {
    // Manually insert expired data (25 hours ago, TTL is 24h)
    const expired = JSON.stringify({ data: 'old', timestamp: Date.now() - 25 * 60 * 60 * 1000 });
    store['@covoit_cache_expired'] = expired;
    const result = await getCached('expired');
    expect(result).toBeNull();
  });

  it('returns valid data within TTL', async () => {
    const fresh = JSON.stringify({ data: 'fresh', timestamp: Date.now() - 10 * 60 * 1000 });
    store['@covoit_cache_recent'] = fresh;
    const result = await getCached('recent');
    expect(result).toBe('fresh');
  });
});

describe('clearCache', () => {
  it('removes all cache keys', async () => {
    store['@covoit_cache_a'] = JSON.stringify({ data: 1, timestamp: Date.now() });
    store['@covoit_cache_b'] = JSON.stringify({ data: 2, timestamp: Date.now() });
    store['other_key'] = 'preserved';

    await clearCache();

    expect(store).not.toHaveProperty('@covoit_cache_a');
    expect(store).not.toHaveProperty('@covoit_cache_b');
    expect(store).toHaveProperty('other_key');
  });
});

describe('fetchWithCache', () => {
  it('returns fresh data on success and caches it', async () => {
    const apiFn = jest.fn().mockResolvedValue({ items: [1, 2, 3] });
    const result = await fetchWithCache('items', apiFn);

    expect(result).toEqual({ data: { items: [1, 2, 3] }, fromCache: false });
    expect(apiFn).toHaveBeenCalledTimes(1);
    // Check it was cached
    const cached = await getCached('items');
    expect(cached).toEqual({ items: [1, 2, 3] });
  });

  it('returns cached data when API fails', async () => {
    await setCache('fallback', { saved: true });
    const apiFn = jest.fn().mockRejectedValue(new Error('Network error'));

    const result = await fetchWithCache('fallback', apiFn);
    expect(result).toEqual({ data: { saved: true }, fromCache: true });
  });

  it('throws when API fails and no cache exists', async () => {
    const apiFn = jest.fn().mockRejectedValue(new Error('Network error'));

    await expect(fetchWithCache('no_cache', apiFn)).rejects.toThrow('Network error');
  });
});
