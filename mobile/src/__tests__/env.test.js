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
    expect(ENV.API_URL_WEB).toBe('http://localhost:8000/api');
    expect(ENV.API_URL_NATIVE).toContain('/api');
  });

  it('exports cache TTL', () => {
    expect(ENV.CACHE_TTL_MS).toBe(30 * 60 * 1000);
  });

  it('getApiUrl returns web URL for web platform', () => {
    expect(getApiUrl()).toBe('http://localhost:8000/api');
  });
});
