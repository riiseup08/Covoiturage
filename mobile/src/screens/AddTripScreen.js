import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Switch, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { Colors, Spacing, Radius } from '../theme';
import Input from '../components/Input';
import Button from '../components/Button';
import { voyages } from '../api/client';
import { useAuth } from '../context/AuthContext';

const CURRENCY_OPTIONS = [
  { value: 'XAF', label: 'FCFA (Afrique Centrale)' },
  { value: 'XOF', label: 'FCFA (Afrique Ouest)' },
  { value: 'NGN', label: 'Naira' },
  { value: 'GHS', label: 'Cedi' },
  { value: 'KES', label: 'Shilling' },
  { value: 'ZAR', label: 'Rand' },
  { value: 'MAD', label: 'Dirham' },
];

const BAGAGE_OPTIONS = [
  { value: 'petit', label: 'Petit (sac à main)' },
  { value: 'moyen', label: 'Moyen (valise cabine)' },
  { value: 'gros', label: 'Gros (valises)' },
  { value: 'tous', label: 'Tous types' },
];

export default function AddTripScreen({ navigation }) {
  const { profileData } = useAuth();
  const isFemale = profileData?.gender === 'female';

  const [form, setForm] = useState({
    ville_depart: '',
    ville_arrivee: '',
    lieu_ramassage: '',
    date_depart: '',
    date_arrivee: '',
    places_disponibles: '3',
    prix_par_place: '',
    currency: 'XAF',
    accept_mobile_money: true,
    accept_cash: true,
    plaque_immatriculation: '',
    modele_voiture: '',
    type_bagage_accepte: 'moyen',
    women_only: false,
  });
  const [loading, setLoading] = useState(false);

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async () => {
    if (!form.ville_depart.trim() || !form.ville_arrivee.trim() || !form.date_depart || !form.prix_par_place) {
      Alert.alert('Erreur', 'Veuillez remplir les champs obligatoires (villes, date départ, prix).');
      return;
    }
    setLoading(true);
    try {
      const data = {
        ...form,
        places_disponibles: parseInt(form.places_disponibles) || 1,
        prix_par_place: parseFloat(form.prix_par_place) || 0,
        date_depart: form.date_depart,
        date_arrivee: form.date_arrivee || form.date_depart,
      };
      await voyages.create(data);
      Alert.alert('Succès', 'Votre trajet a été publié !');
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
          <Text style={styles.sectionLabel}>📍 Itinéraire</Text>
          <Input label="Ville de départ *" placeholder="ex: Douala" value={form.ville_depart} onChangeText={v => update('ville_depart', v)} />
          <Input label="Ville d'arrivée *" placeholder="ex: Yaoundé" value={form.ville_arrivee} onChangeText={v => update('ville_arrivee', v)} />
          <Input label="Lieu de ramassage" placeholder="Détails du point de rencontre" value={form.lieu_ramassage} onChangeText={v => update('lieu_ramassage', v)} />

          <Text style={styles.sectionLabel}>📅 Horaires</Text>
          <Input label="Date/heure de départ *" placeholder="2026-03-25T08:00:00" value={form.date_depart} onChangeText={v => update('date_depart', v)} />
          <Input label="Date/heure d'arrivée" placeholder="2026-03-25T12:00:00" value={form.date_arrivee} onChangeText={v => update('date_arrivee', v)} />

          <Text style={styles.sectionLabel}>💰 Tarification</Text>
          <Input label="Places disponibles" placeholder="3" value={form.places_disponibles} onChangeText={v => update('places_disponibles', v)} keyboardType="numeric" />
          <Input label="Prix par place *" placeholder="5000" value={form.prix_par_place} onChangeText={v => update('prix_par_place', v)} keyboardType="numeric" />

          <Text style={styles.pickerLabel}>Devise</Text>
          <View style={styles.chipRow}>
            {CURRENCY_OPTIONS.map(c => (
              <Text
                key={c.value}
                style={[styles.chip, form.currency === c.value && styles.chipActive]}
                onPress={() => update('currency', c.value)}
              >
                {c.label}
              </Text>
            ))}
          </View>

          <SwitchRow label="📱 Accepter Mobile Money" value={form.accept_mobile_money} onValueChange={v => update('accept_mobile_money', v)} />
          <SwitchRow label="💵 Accepter les espèces" value={form.accept_cash} onValueChange={v => update('accept_cash', v)} />

          {isFemale && (
            <SwitchRow label="👩 Trajet réservé aux femmes" value={form.women_only} onValueChange={v => update('women_only', v)} />
          )}

          <Text style={styles.sectionLabel}>🚗 Véhicule & Bagages</Text>
          <Input label="Plaque d'immatriculation" placeholder="AB-123-CD" value={form.plaque_immatriculation} onChangeText={v => update('plaque_immatriculation', v)} />
          <Input label="Modèle de voiture" placeholder="Toyota Corolla" value={form.modele_voiture} onChangeText={v => update('modele_voiture', v)} />

          <Text style={styles.pickerLabel}>Bagages acceptés</Text>
          <View style={styles.chipRow}>
            {BAGAGE_OPTIONS.map(b => (
              <Text
                key={b.value}
                style={[styles.chip, form.type_bagage_accepte === b.value && styles.chipActive]}
                onPress={() => update('type_bagage_accepte', b.value)}
              >
                {b.label}
              </Text>
            ))}
          </View>

          <Button title="Publier le trajet" onPress={handleSubmit} loading={loading} style={{ marginTop: Spacing.lg }} />
          <View style={{ height: 40 }} />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function SwitchRow({ label, value, onValueChange }) {
  return (
    <View style={styles.switchRow}>
      <Text style={styles.switchLabel}>{label}</Text>
      <Switch value={value} onValueChange={onValueChange} trackColor={{ true: Colors.earth, false: Colors.border }} thumbColor={Colors.white} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.lg },
  sectionLabel: { fontSize: 16, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.sm, marginTop: Spacing.md },
  pickerLabel: { fontSize: 14, fontWeight: '600', color: Colors.text, marginBottom: Spacing.xs },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs, marginBottom: Spacing.md },
  chip: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: Radius.full,
    backgroundColor: Colors.bgCard, borderWidth: 1, borderColor: Colors.border,
    fontSize: 12, color: Colors.textLight,
  },
  chipActive: { backgroundColor: Colors.earth, borderColor: Colors.earth, color: Colors.white },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: Spacing.sm },
  switchLabel: { fontSize: 14, color: Colors.text, flex: 1 },
});
