import React from 'react';
import { View, Text, TextInput as RNTextInput, StyleSheet } from 'react-native';
import { Colors, Radius, Spacing } from '../theme';

/**
 * @param {object} props
 * @param {string} [props.label] - Label text above the input
 * @param {string} [props.error] - Error message below the input
 * @param {import('react-native').ViewStyle} [props.style] - Wrapper style override
 * @param {string} [props.placeholder] - Placeholder text
 * @param {string} [props.value] - Current input value
 * @param {(text: string) => void} [props.onChangeText] - Text change handler
 */
export default function Input({ label, error, style, ...props }) {
  return (
    <View style={[styles.wrapper, style]}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <RNTextInput
        style={[styles.input, error && styles.inputError]}
        placeholderTextColor={Colors.textMuted}
        accessibilityLabel={label || props.placeholder}
        accessibilityHint={error || undefined}
        accessibilityState={{ disabled: props.editable === false }}
        {...props}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { marginBottom: Spacing.md },
  label: { fontSize: 14, fontWeight: '600', color: Colors.text, marginBottom: Spacing.xs },
  input: {
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.md - 4,
    fontSize: 15,
    color: Colors.text,
    backgroundColor: Colors.bgCard,
    minHeight: 48,
  },
  inputError: { borderColor: Colors.danger },
  error: { fontSize: 12, color: Colors.danger, marginTop: Spacing.xs },
});
