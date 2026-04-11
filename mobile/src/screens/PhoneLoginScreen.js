import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Colors, Spacing, Radius } from '../theme';
import Input from '../components/Input';
import Button from '../components/Button';
import { auth } from '../api/client';
import { useI18n } from '../i18n';

export default function PhoneLoginScreen({ navigation }) {
  const { t } = useI18n();
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const cooldownRef = useRef(null);

  useEffect(() => {
    if (cooldown > 0) {
      cooldownRef.current = setTimeout(() => setCooldown(c => c - 1), 1000);
    }
    return () => clearTimeout(cooldownRef.current);
  }, [cooldown]);

  const handleSendOtp = async () => {
    const cleaned = phone.trim().replace(/\s+/g, '');
    const phoneRegex = /^(\+?237)?[26]\d{7,8}$/;
    if (!cleaned || !phoneRegex.test(cleaned)) {
      setError(t('phoneFormatInvalid'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await auth.phoneRequestOtp(cleaned);
      setCooldown(60);
      navigation.navigate('PhoneVerify', { phone: data.phone });
    } catch (e) {
      setError(e.message || t('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.logo}>📱</Text>
          <Text style={styles.title}>{t('phoneLogin')}</Text>
          <Text style={styles.subtitle}>{t('countryLabel')}</Text>
        </View>

        <View style={styles.form}>
          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          <Input
            label={t('phoneNumber')}
            placeholder={t('phonePlaceholder')}
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
            autoCapitalize="none"
          />

          <Button title={cooldown > 0 ? `${t('sendCode')} (${cooldown}s)` : t('sendCode')} onPress={handleSendOtp} loading={loading} disabled={cooldown > 0} />

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>{t('or')}</Text>
            <View style={styles.dividerLine} />
          </View>

          <Button
            title={t('usePassword')}
            variant="secondary"
            onPress={() => navigation.navigate('Login')}
          />

          <View style={styles.linkRow}>
            <Text style={styles.linkText}>{t('noAccount')}</Text>
            <Text style={styles.link} onPress={() => navigation.navigate('Register')}>{t('register')}</Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: Spacing.lg },
  header: { alignItems: 'center', marginBottom: Spacing.xl },
  logo: { fontSize: 48 },
  title: { fontSize: 24, fontWeight: 'bold', color: Colors.earth, marginTop: Spacing.sm },
  subtitle: { fontSize: 13, color: Colors.textMuted, marginTop: Spacing.xs },
  form: {
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.lg,
    padding: Spacing.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  errorText: {
    backgroundColor: Colors.danger + '15',
    color: Colors.danger,
    padding: Spacing.sm,
    borderRadius: Radius.sm,
    marginBottom: Spacing.md,
    fontSize: 13,
    textAlign: 'center',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: Spacing.md,
  },
  dividerLine: { flex: 1, height: 1, backgroundColor: Colors.borderLight },
  dividerText: { paddingHorizontal: Spacing.sm, color: Colors.textMuted, fontSize: 12 },
  linkRow: { flexDirection: 'row', justifyContent: 'center', marginTop: Spacing.lg },
  linkText: { color: Colors.textLight, fontSize: 14 },
  link: { color: Colors.earth, fontSize: 14, fontWeight: '600' },
});
