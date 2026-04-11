/**
 * Jest setup file — runs before each test file.
 */
global.__DEV__ = true;

// Mock expo-constants for env.js
jest.mock('expo-constants', () => ({
  expoConfig: { extra: {} },
}));
