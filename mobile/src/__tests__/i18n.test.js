/**
 * Tests for mobile/src/i18n/index.js
 *
 * Run: npx jest src/__tests__/i18n.test.js
 */

jest.mock('react-native', () => ({
  Platform: { OS: 'web' },
}));

const en = require('../i18n/en').default;
const fr = require('../i18n/fr').default;

describe('Translation files', () => {
  it('French file has all keys from English file', () => {
    const enKeys = Object.keys(en);
    const frKeys = Object.keys(fr);
    const missingInFr = enKeys.filter(k => !frKeys.includes(k));
    expect(missingInFr).toEqual([]);
  });

  it('English file has all keys from French file', () => {
    const enKeys = Object.keys(en);
    const frKeys = Object.keys(fr);
    const missingInEn = frKeys.filter(k => !enKeys.includes(k));
    expect(missingInEn).toEqual([]);
  });

  it('no empty translation values in French', () => {
    const emptyKeys = Object.entries(fr).filter(([, v]) => v === '').map(([k]) => k);
    expect(emptyKeys).toEqual([]);
  });

  it('no empty translation values in English', () => {
    const emptyKeys = Object.entries(en).filter(([, v]) => v === '').map(([k]) => k);
    expect(emptyKeys).toEqual([]);
  });

  it('common keys exist in both languages', () => {
    const requiredKeys = [
      'loading', 'error', 'success', 'cancel', 'save', 'delete', 'confirm',
      'login', 'register', 'logout', 'greeting', 'search', 'wallet',
      'loadErrorMessage', 'offlineBanner',
    ];
    for (const key of requiredKeys) {
      expect(en).toHaveProperty(key);
      expect(fr).toHaveProperty(key);
    }
  });
});
