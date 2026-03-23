import React from 'react';
import { View, Text, TextInput as RNTextInput, StyleSheet } from 'react-native';
import { Colors, Radius, Spacing } from '../theme';

export default function Input({ label, error, style, ...props }) {
  return (
    <View style={[styles.wrapper, style]}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <RNTextInput
        style={[styles.input, error && styles.inputError]}
        placeholderTextColor={Colors.textMuted}
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
