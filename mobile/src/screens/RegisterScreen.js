import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Colors, Spacing, Radius } from '../theme';
import Input from '../components/Input';
import Button from '../components/Button';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';

export default function RegisterScreen({ navigation }) {
  const { register } = useAuth();
  const { t } = useI18n();
  const [form, setForm] = useState({ username: '', email: '', password: '', first_name: '', last_name: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleRegister = async () => {
    if (!form.username.trim() || !form.email.trim() || !form.password) {
      setError(t('fillRequired'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      await register({
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
      });
    } catch (e) {
      setError(e.message || t('registerError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.logo}>🚗</Text>
          <Text style={styles.title}>{t('createAccount')}</Text>
        </View>

        <View style={styles.form}>
          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          <Input label={t('usernameRequired')} placeholder={t('usernamePlaceholder')} value={form.username} onChangeText={v => update('username', v)} autoCapitalize="none" />
          <Input label={t('emailRequired')} placeholder={t('emailPlaceholder')} value={form.email} onChangeText={v => update('email', v)} keyboardType="email-address" autoCapitalize="none" />
          <Input label={t('passwordRequired')} placeholder={t('passwordPlaceholder')} value={form.password} onChangeText={v => update('password', v)} secureTextEntry />
          <Input label={t('firstName')} placeholder="Jean" value={form.first_name} onChangeText={v => update('first_name', v)} />
          <Input label={t('lastName')} placeholder="Doe" value={form.last_name} onChangeText={v => update('last_name', v)} />

          <Button title={t('register')} onPress={handleRegister} loading={loading} />

          <View style={styles.linkRow}>
            <Text style={styles.linkText}>{t('hasAccount')}</Text>
            <Text style={styles.link} onPress={() => navigation.navigate('Login')}>{t('login')}</Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: Spacing.lg },
  header: { alignItems: 'center', marginBottom: Spacing.lg },
  logo: { fontSize: 48 },
  title: { fontSize: 24, fontWeight: 'bold', color: Colors.earth, marginTop: Spacing.sm },
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
  linkRow: { flexDirection: 'row', justifyContent: 'center', marginTop: Spacing.lg },
  linkText: { color: Colors.textLight, fontSize: 14 },
  link: { color: Colors.earth, fontSize: 14, fontWeight: '600' },
});
