import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Colors, Spacing, Radius } from '../theme';
import Input from '../components/Input';
import Button from '../components/Button';
import { auth, saveToken } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';

export default function PhoneVerifyScreen({ route, navigation }) {
  const { t } = useI18n();
  const { refreshAfterPhoneLogin } = useAuth();
  const phone = route.params?.phone || '';
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendTimer, setResendTimer] = useState(60);
  const [needsRegister, setNeedsRegister] = useState(false);
  const [username, setUsername] = useState('');

  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleVerify = async () => {
    if (!code.trim() || code.trim().length !== 6) {
      setError(t('otpInvalid'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await auth.phoneVerifyOtp(phone, code.trim());
      if (data.status === 'authenticated') {
        await saveToken(data.token);
        refreshAfterPhoneLogin(data);
      } else if (data.status === 'needs_register') {
        setNeedsRegister(true);
      }
    } catch (e) {
      setError(e.message || t('otpInvalid'));
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneRegister = async () => {
    if (!username.trim()) {
      setError(t('fillRequired'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await auth.phoneRegister({ phone, username: username.trim() });
      await saveToken(data.token);
      refreshAfterPhoneLogin(data);
    } catch (e) {
      setError(e.message || t('registerError'));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      await auth.phoneRequestOtp(phone);
      setResendTimer(60);
      setError('');
    } catch (e) {
      setError(e.message || t('otpResendFailed'));
    }
  };

  if (needsRegister) {
    return (
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <Text style={styles.logo}>👤</Text>
            <Text style={styles.title}>{t('completeProfile')}</Text>
            <Text style={styles.subtitle}>{phone}</Text>
          </View>
          <View style={styles.form}>
            {error ? <Text style={styles.errorText}>{error}</Text> : null}
            <Input
              label={t('username') + ' *'}
              placeholder="ex: jean_doe"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
            />
            <Button title={t('register')} onPress={handlePhoneRegister} loading={loading} />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.logo}>🔐</Text>
          <Text style={styles.title}>{t('verifyCode')}</Text>
          <Text style={styles.subtitle}>{t('otpSent')} {phone}</Text>
        </View>

        <View style={styles.form}>
          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          <Input
            label={t('otpCode')}
            placeholder={t('otpPlaceholder')}
            value={code}
            onChangeText={setCode}
            keyboardType="number-pad"
            maxLength={6}
            autoFocus
          />

          <Button title={t('verifyCode')} onPress={handleVerify} loading={loading} />

          <View style={styles.resendRow}>
            {resendTimer > 0 ? (
              <Text style={styles.resendTimer}>{t('otpResend')} ({resendTimer}s)</Text>
            ) : (
              <Text style={styles.resendLink} onPress={handleResend}>{t('otpResend')}</Text>
            )}
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
  subtitle: { fontSize: 13, color: Colors.textMuted, marginTop: Spacing.xs, textAlign: 'center' },
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
  resendRow: { alignItems: 'center', marginTop: Spacing.lg },
  resendTimer: { color: Colors.textMuted, fontSize: 13 },
  resendLink: { color: Colors.earth, fontSize: 14, fontWeight: '600' },
});
