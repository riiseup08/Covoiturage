// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// Ensure 'web' is a recognized platform so .web.js extensions resolve
if (!config.resolver.platforms.includes('web')) {
  config.resolver.platforms.push('web');
}

// Alias react-native → react-native-web for web bundles
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web') {
    // Top-level 'react-native' import → redirect to react-native-web
    if (moduleName === 'react-native') {
      return context.resolveRequest(context, 'react-native-web', platform);
    }
    // Internal react-native relative imports (e.g. ../Utilities/Platform)
    // should also redirect when originating from react-native package
    if (
      context.originModulePath &&
      context.originModulePath.includes(path.join('node_modules', 'react-native') + path.sep) &&
      !context.originModulePath.includes(path.join('node_modules', 'react-native-web'))
    ) {
      // Let react-native-web handle it via top-level redirect
      try {
        return context.resolveRequest(context, 'react-native-web', platform);
      } catch {
        // Fall through to default resolution
      }
    }
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
