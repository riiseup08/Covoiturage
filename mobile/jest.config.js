module.exports = {
  preset: 'jest-expo',
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)/|expo(nent)?/|@expo(nent)?/.*|react-navigation|@react-navigation/.*)',
  ],
  setupFiles: ['./src/__tests__/setup.js'],
  testPathIgnorePatterns: ['/node_modules/', 'setup\\.js$'],
};
