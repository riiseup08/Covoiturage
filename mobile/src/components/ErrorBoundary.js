import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors, Spacing, Radius } from '../theme';
import logger from '../utils/logger';

export default class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    logger.error('ErrorBoundary', error.message, error);
    // TODO: Send to Sentry/Bugsnag when configured
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <Text style={styles.icon}>⚠️</Text>
          <Text style={styles.title}>Oops!</Text>
          <Text style={styles.message}>
            Something went wrong. Please try again.
          </Text>
          <TouchableOpacity style={styles.button} onPress={this.handleReset}>
            <Text style={styles.buttonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    backgroundColor: Colors.bg, padding: Spacing.xl,
  },
  icon: { fontSize: 48, marginBottom: Spacing.md },
  title: { fontSize: 22, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.sm },
  message: { fontSize: 14, color: Colors.textLight, textAlign: 'center', marginBottom: Spacing.lg },
  button: {
    backgroundColor: Colors.earth, paddingHorizontal: 24, paddingVertical: 12,
    borderRadius: Radius.md,
  },
  buttonText: { color: Colors.white, fontWeight: '600', fontSize: 15 },
});
