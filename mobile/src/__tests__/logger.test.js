/**
 * Tests for mobile/src/utils/logger.js
 */

// Set __DEV__ for testing
global.__DEV__ = true;

const logger = require('../utils/logger').default;

beforeEach(() => {
  jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.spyOn(console, 'info').mockImplementation(() => {});
  jest.spyOn(console, 'warn').mockImplementation(() => {});
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('logger', () => {
  it('logger.debug outputs to console.log in dev', () => {
    logger.debug('Test', 'debug message');
    expect(console.log).toHaveBeenCalledTimes(1);
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('[DEBUG] [Test]'),
      'debug message',
      ''
    );
  });

  it('logger.info outputs to console.info', () => {
    logger.info('API', 'request sent', { url: '/test' });
    expect(console.info).toHaveBeenCalledTimes(1);
    expect(console.info).toHaveBeenCalledWith(
      expect.stringContaining('[INFO] [API]'),
      'request sent',
      { url: '/test' }
    );
  });

  it('logger.warn outputs to console.warn', () => {
    logger.warn('Cache', 'miss');
    expect(console.warn).toHaveBeenCalledTimes(1);
  });

  it('logger.error outputs to console.error', () => {
    const err = new Error('fail');
    logger.error('Auth', 'token refresh failed', err);
    expect(console.error).toHaveBeenCalledTimes(1);
    expect(console.error).toHaveBeenCalledWith(
      expect.stringContaining('[ERROR] [Auth]'),
      'token refresh failed',
      err
    );
  });
});
