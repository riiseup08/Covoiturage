import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { Colors, Spacing } from '../theme';
import Input from '../components/Input';
import DatePicker from '../components/DatePicker';
import Button from '../components/Button';
import { demandes } from '../api/client';
import { useI18n } from '../i18n';

export default function AddDemandeScreen({ navigation }) {
  const { t } = useI18n();
  const [form, setForm] = useState({ ville_depart: '', ville_arrivee: '', date_voyage: '', places: '1' });
  const [loading, setLoading] = useState(false);

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async () => {
    if (!form.ville_depart.trim() || !form.ville_arrivee.trim() || !form.date_voyage) {
      Alert.alert(t('error'), t('fillRequiredDemande'));
      return;
    }
    setLoading(true);
    try {
      await demandes.create({
        ...form,
        places: parseInt(form.places) || 1,
      });
      Alert.alert(t('success'), t('requestPublished'));
      navigation.goBack();
    } catch (e) {
      Alert.alert(t('error'), e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.content}>
          <Text style={styles.title}>🔍 {t('postTripRequest')}</Text>
          <Input label={t('departureCity')} placeholder="ex: Bamenda" value={form.ville_depart} onChangeText={v => update('ville_depart', v)} />
          <Input label={t('arrivalCity')} placeholder="ex: Buea" value={form.ville_arrivee} onChangeText={v => update('ville_arrivee', v)} />
          <DatePicker label={t('travelDate')} value={form.date_voyage} onChange={v => update('date_voyage', v)} mode="date" placeholder="2026-03-25" />
          <Input label={t('numberOfSeats')} placeholder="1" value={form.places} onChangeText={v => update('places', v)} keyboardType="numeric" />

          <Button title={t('publishRequest')} onPress={handleSubmit} loading={loading} style={{ marginTop: Spacing.lg }} />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.lg },
  title: { fontSize: 18, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.lg },
});
