/**
 * Tests for mobile/src/api/client.js
 *
 * Run: npx jest src/__tests__/client.test.js
 */

global.__DEV__ = true;

jest.mock('react-native', () => ({
  Platform: { OS: 'web' },
}));

// Mock localStorage
const localStore = {};
global.localStorage = {
  getItem: jest.fn((key) => localStore[key] || null),
  setItem: jest.fn((key, val) => { localStore[key] = val; }),
  removeItem: jest.fn((key) => { delete localStore[key]; }),
};

// Mock fetch
global.fetch = jest.fn();

const { loadToken, saveToken, clearToken, getToken, auth, voyages, profile, onTokenExpired } = require('../api/client');

beforeEach(() => {
  Object.keys(localStore).forEach(k => delete localStore[k]);
  jest.clearAllMocks();
});

describe('Token management (web)', () => {
  it('saveToken stores and getToken returns it', async () => {
    await saveToken('abc123');
    expect(getToken()).toBe('abc123');
    expect(localStorage.setItem).toHaveBeenCalledWith('auth_token', 'abc123');
  });

  it('loadToken reads from localStorage', async () => {
    localStore['auth_token'] = 'saved_token';
    const token = await loadToken();
    expect(token).toBe('saved_token');
  });

  it('clearToken removes the token', async () => {
    await saveToken('temp');
    await clearToken();
    expect(getToken()).toBeNull();
    expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token');
  });
});

describe('API request', () => {
  it('auth.login sends POST with credentials', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ token: 'tok', username: 'jean', user_id: 1 }),
    });

    const result = await auth.login('jean', 'pass123');
    expect(result).toEqual({ token: 'tok', username: 'jean', user_id: 1 });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login/'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'jean', password: 'pass123' }),
      })
    );
  });

  it('throws on non-ok response with error message', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ error: 'Invalid credentials' }),
    });

    await expect(auth.login('bad', 'creds')).rejects.toThrow('Invalid credentials');
  });

  it('returns null for 204 responses', async () => {
    await saveToken('tok');
    global.fetch.mockResolvedValue({
      ok: true,
      status: 204,
    });

    const result = await voyages.delete(5);
    expect(result).toBeNull();
  });

  it('sends Authorization header when token is set', async () => {
    await saveToken('my_token');
    global.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ username: 'jean' }),
    });

    await profile.me();
    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer my_token',
        }),
      })
    );
  });

  it('calls onTokenExpired callback and throws on 401', async () => {
    await saveToken('expired_token');
    const expiredCb = jest.fn();
    onTokenExpired(expiredCb);

    global.fetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid token.' }),
    });

    await expect(profile.me()).rejects.toThrow('Session expired');
    expect(expiredCb).toHaveBeenCalledTimes(1);
    expect(getToken()).toBeNull();
  });
});
