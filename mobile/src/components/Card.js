import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Colors, Radius, Spacing } from '../theme';

/**
 * @param {object} props
 * @param {React.ReactNode} props.children - Card content
 * @param {import('react-native').ViewStyle} [props.style] - Additional container style
 */
export default function Card({ children, style }) {
  return <View style={[styles.card, style]} accessible={true} accessibilityRole="summary">{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
});
