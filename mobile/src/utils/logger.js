/**
 * Lightweight logger for the app.
 * Logs are written to the console in __DEV__ mode.
 * In production, errors are captured for future remote reporting.
 *
 * Usage:
 *   import logger from '../utils/logger';
 *   logger.error('AuthContext', 'Token refresh failed', err);
 *   logger.warn('Offline', 'Using cached data');
 *   logger.info('Payment', 'Transaction created', { id: 42 });
 */

const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };
const CURRENT_LEVEL = __DEV__ ? LOG_LEVELS.debug : LOG_LEVELS.warn;

function formatMessage(level, tag, message, data) {
  const ts = new Date().toISOString();
  const prefix = `[${ts}] [${level.toUpperCase()}] [${tag}]`;
  return { prefix, message, data };
}

const logger = {
  debug(tag, message, data) {
    if (CURRENT_LEVEL > LOG_LEVELS.debug) return;
    const { prefix } = formatMessage('debug', tag, message, data);
    console.log(prefix, message, data !== undefined ? data : '');
  },

  info(tag, message, data) {
    if (CURRENT_LEVEL > LOG_LEVELS.info) return;
    const { prefix } = formatMessage('info', tag, message, data);
    console.info(prefix, message, data !== undefined ? data : '');
  },

  warn(tag, message, data) {
    if (CURRENT_LEVEL > LOG_LEVELS.warn) return;
    const { prefix } = formatMessage('warn', tag, message, data);
    console.warn(prefix, message, data !== undefined ? data : '');
  },

  error(tag, message, error) {
    if (CURRENT_LEVEL > LOG_LEVELS.error) return;
    const { prefix } = formatMessage('error', tag, message, error);
    console.error(prefix, message, error || '');
    // TODO: Send to remote error reporting service (Sentry, Bugsnag, etc.)
  },
};

export default logger;
