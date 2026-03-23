import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Colors, Radius, Spacing } from '../theme';

export default function Button({ title, onPress, variant = 'primary', loading = false, style, textStyle, disabled }) {
  const isPrimary = variant === 'primary';
  const isDanger = variant === 'danger';

  return (
    <TouchableOpacity
      style={[
        styles.btn,
        isPrimary && styles.primary,
        isDanger && styles.danger,
        !isPrimary && !isDanger && styles.secondary,
        (disabled || loading) && styles.disabled,
        style,
      ]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator color={isPrimary || isDanger ? Colors.white : Colors.earth} />
      ) : (
        <Text style={[styles.text, isPrimary && styles.textPrimary, isDanger && styles.textDanger, !isPrimary && !isDanger && styles.textSecondary, textStyle]}>
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  btn: {
    paddingVertical: Spacing.md - 2,
    paddingHorizontal: Spacing.lg,
    borderRadius: Radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  primary: { backgroundColor: Colors.earth },
  secondary: { backgroundColor: Colors.bgCard, borderWidth: 1.5, borderColor: Colors.earth },
  danger: { backgroundColor: Colors.danger },
  disabled: { opacity: 0.5 },
  text: { fontSize: 16, fontWeight: '600' },
  textPrimary: { color: Colors.white },
  textSecondary: { color: Colors.earth },
  textDanger: { color: Colors.white },
});
