import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Colors, Spacing, Radius } from '../theme';
import Input from '../components/Input';
import Button from '../components/Button';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';

export default function LoginScreen({ navigation }) {
  const { login } = useAuth();
  const { t, lang, setLang } = useI18n();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!username.trim() || !password) {
      setError(t('fillAllFields'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      await login(username.trim(), password);
    } catch (e) {
      setError(e.message || t('loginError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        {/* Language toggle */}
        <View style={styles.langRow}>
          <Text
            style={[styles.langBtn, lang === 'fr' && styles.langActive]}
            onPress={() => setLang('fr')}
            accessibilityRole="button"
            accessibilityLabel="Français"
            accessibilityState={{ selected: lang === 'fr' }}
          >FR</Text>
          <Text
            style={[styles.langBtn, lang === 'en' && styles.langActive]}
            onPress={() => setLang('en')}
            accessibilityRole="button"
            accessibilityLabel="English"
            accessibilityState={{ selected: lang === 'en' }}
          >EN</Text>
        </View>

        <View style={styles.header}>
          <Text style={styles.logo}>🚗</Text>
          <Text style={styles.title}>Covoiturage</Text>
          <Text style={styles.subtitle}>{t('login')}</Text>
        </View>

        <View style={styles.form}>
          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          <Input
            label={t('username')}
            placeholder={t('username')}
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Input
            label={t('password')}
            placeholder={t('password')}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
          <Button title={t('login')} onPress={handleLogin} loading={loading} />

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>ou</Text>
            <View style={styles.dividerLine} />
          </View>

          <Button
            title={t('usePhone')}
            variant="secondary"
            onPress={() => navigation.navigate('PhoneLogin')}
          />

          <View style={styles.linkRow}>
            <Text style={styles.linkText}>{t('noAccount')}</Text>
            <Text style={styles.link} onPress={() => navigation.navigate('Register')} accessibilityRole="link">{t('register')}</Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: Spacing.lg },
  langRow: {
    flexDirection: 'row', justifyContent: 'center', gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  langBtn: {
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: Radius.full,
    borderWidth: 1, borderColor: Colors.border, color: Colors.textMuted,
    fontSize: 13, fontWeight: '600', overflow: 'hidden',
  },
  langActive: {
    backgroundColor: Colors.earth, borderColor: Colors.earth, color: Colors.white,
  },
  header: { alignItems: 'center', marginBottom: Spacing.xl },
  logo: { fontSize: 48 },
  title: { fontSize: 28, fontWeight: 'bold', color: Colors.earth, marginTop: Spacing.sm },
  subtitle: { fontSize: 14, color: Colors.textLight, marginTop: Spacing.xs },
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
