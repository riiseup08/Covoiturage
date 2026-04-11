/**
 * Tests for mobile/src/config/env.js
 */

jest.mock('react-native', () => ({
  Platform: { OS: 'web' },
}));

const ENV = require('../config/env').default;
const { getApiUrl } = require('../config/env');

describe('env config', () => {
  it('exports API URLs', () => {
    expect(ENV.API_URL_PRODUCTION).toBe('https://api.covoitafrica.com/api');
    expect(ENV.API_URL_WEB_DEV).toBe('http://localhost:8000/api');
    expect(ENV.API_URL_NATIVE_DEV).toContain('/api');
  });

  it('exports cache TTL', () => {
    expect(ENV.CACHE_TTL_MS).toBe(24 * 60 * 60 * 1000);
  });

  it('getApiUrl returns dev web URL in __DEV__ mode', () => {
    // __DEV__ is true in test env, no EXPO_PUBLIC_API_URL set
    expect(getApiUrl()).toBe('http://localhost:8000/api');
  });
});
