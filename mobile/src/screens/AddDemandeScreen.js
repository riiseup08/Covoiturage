import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { Colors, Spacing } from '../theme';
import Input from '../components/Input';
import Button from '../components/Button';
import { demandes } from '../api/client';

export default function AddDemandeScreen({ navigation }) {
  const [form, setForm] = useState({ ville_depart: '', ville_arrivee: '', date_voyage: '', places: '1' });
  const [loading, setLoading] = useState(false);

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async () => {
    if (!form.ville_depart.trim() || !form.ville_arrivee.trim() || !form.date_voyage) {
      Alert.alert('Erreur', 'Veuillez remplir tous les champs obligatoires.');
      return;
    }
    setLoading(true);
    try {
      await demandes.create({
        ...form,
        places: parseInt(form.places) || 1,
      });
      Alert.alert('Succès', 'Votre demande a été publiée !');
      navigation.goBack();
    } catch (e) {
      Alert.alert('Erreur', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.content}>
          <Text style={styles.title}>🔍 Poster une demande de trajet</Text>
          <Input label="Ville de départ *" placeholder="ex: Bamenda" value={form.ville_depart} onChangeText={v => update('ville_depart', v)} />
          <Input label="Ville d'arrivée *" placeholder="ex: Buea" value={form.ville_arrivee} onChangeText={v => update('ville_arrivee', v)} />
          <Input label="Date du voyage *" placeholder="2026-03-25" value={form.date_voyage} onChangeText={v => update('date_voyage', v)} />
          <Input label="Nombre de places" placeholder="1" value={form.places} onChangeText={v => update('places', v)} keyboardType="numeric" />

          <Button title="Publier la demande" onPress={handleSubmit} loading={loading} style={{ marginTop: Spacing.lg }} />
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
