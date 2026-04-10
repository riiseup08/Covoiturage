import React, { useState } from 'react';
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

  const handleSendOtp = async () => {
    const cleaned = phone.trim();
    if (!cleaned) {
      setError(t('phoneInvalid'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await auth.phoneRequestOtp(cleaned);
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
          <Text style={styles.subtitle}>Cameroun (+237)</Text>
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

          <Button title={t('sendCode')} onPress={handleSendOtp} loading={loading} />

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>ou</Text>
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
