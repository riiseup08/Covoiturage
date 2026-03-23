import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import { Colors, Spacing, Radius } from '../theme';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import { profile as profileApi } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function ProfileScreen() {
  const { profileData, refreshProfile } = useAuth();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useFocusEffect(useCallback(() => { refreshProfile(); }, []));

  const startEdit = () => {
    setForm({
      bio: profileData?.bio || '',
      phone: profileData?.phone || '',
      gender: profileData?.gender || '',
      emergency_contact_name: profileData?.emergency_contact_name || '',
      emergency_contact_phone: profileData?.emergency_contact_phone || '',
      whatsapp_number: profileData?.whatsapp_number || '',
      mobile_money_number: profileData?.mobile_money_number || '',
      mobile_money_provider: profileData?.mobile_money_provider || '',
    });
    setEditing(true);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await profileApi.update(form);
      await refreshProfile();
      setEditing(false);
      Alert.alert('Succès', 'Profil mis à jour !');
    } catch (e) {
      Alert.alert('Erreur', e.message);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshProfile();
    setRefreshing(false);
  };

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }));
  const p = profileData || {};

  const VerifBadge = ({ verified, label }) => (
    <View style={[styles.verifBadge, verified && styles.verifOk]}>
      <Ionicons name={verified ? 'checkmark-circle' : 'close-circle'} size={14} color={verified ? Colors.success : Colors.textMuted} />
      <Text style={[styles.verifText, verified && { color: Colors.success }]}>{label}</Text>
    </View>
  );

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.earth} />}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={40} color={Colors.white} />
          </View>
          <Text style={styles.username}>{p.username}</Text>
          <Text style={styles.email}>{p.email}</Text>
          <View style={styles.badges}>
            <VerifBadge verified={p.id_verified} label="ID" />
            <VerifBadge verified={p.phone_verified} label="Téléphone" />
            <VerifBadge verified={p.driver_license_verified} label="Permis" />
          </View>
          {p.avg_rating && (
            <View style={styles.ratingRow}>
              <Ionicons name="star" size={16} color={Colors.star} />
              <Text style={styles.ratingText}>{p.avg_rating}/5 ({p.review_count} avis)</Text>
            </View>
          )}
        </View>

        {!editing ? (
          <>
            {/* View mode */}
            <Card>
              <Text style={styles.sectionTitle}>Informations personnelles</Text>
              <InfoRow label="Genre" value={p.gender === 'male' ? 'Homme' : p.gender === 'female' ? 'Femme' : '—'} />
              <InfoRow label="Téléphone" value={p.phone || '—'} />
              <InfoRow label="WhatsApp" value={p.whatsapp_number || '—'} />
              <InfoRow label="Bio" value={p.bio || '—'} />
            </Card>

            <Card>
              <Text style={styles.sectionTitle}>Contact d'urgence</Text>
              <InfoRow label="Nom" value={p.emergency_contact_name || '—'} />
              <InfoRow label="Téléphone" value={p.emergency_contact_phone || '—'} />
            </Card>

            <Card>
              <Text style={styles.sectionTitle}>Mobile Money</Text>
              <InfoRow label="Numéro" value={p.mobile_money_number || '—'} />
              <InfoRow label="Fournisseur" value={p.mobile_money_provider || '—'} />
            </Card>

            <Button title="Modifier le profil" onPress={startEdit} style={{ marginTop: Spacing.sm }} />
          </>
        ) : (
          <>
            {/* Edit mode */}
            <Card>
              <Text style={styles.sectionTitle}>✏️ Modifier le profil</Text>
              <Input label="Bio" value={form.bio} onChangeText={v => update('bio', v)} multiline />
              <Input label="Téléphone" value={form.phone} onChangeText={v => update('phone', v)} keyboardType="phone-pad" />
              <Input label="WhatsApp" value={form.whatsapp_number} onChangeText={v => update('whatsapp_number', v)} keyboardType="phone-pad" />

              <Text style={styles.pickerLabel}>Genre</Text>
              <View style={styles.chipRow}>
                {[{ v: 'male', l: 'Homme' }, { v: 'female', l: 'Femme' }].map(g => (
                  <Text
                    key={g.v}
                    style={[styles.chip, form.gender === g.v && styles.chipActive]}
                    onPress={() => update('gender', g.v)}
                  >
                    {g.l}
                  </Text>
                ))}
              </View>

              <Input label="Contact d'urgence (nom)" value={form.emergency_contact_name} onChangeText={v => update('emergency_contact_name', v)} />
              <Input label="Contact d'urgence (tél)" value={form.emergency_contact_phone} onChangeText={v => update('emergency_contact_phone', v)} keyboardType="phone-pad" />
              <Input label="Mobile Money (numéro)" value={form.mobile_money_number} onChangeText={v => update('mobile_money_number', v)} keyboardType="phone-pad" />

              <Text style={styles.pickerLabel}>Fournisseur Mobile Money</Text>
              <View style={styles.chipRow}>
                {['mtn', 'orange', 'moov', 'airtel', 'wave', 'other'].map(prov => (
                  <Text
                    key={prov}
                    style={[styles.chip, form.mobile_money_provider === prov && styles.chipActive]}
                    onPress={() => update('mobile_money_provider', prov)}
                  >
                    {prov.toUpperCase()}
                  </Text>
                ))}
              </View>
            </Card>

            <View style={styles.editActions}>
              <Button title="Annuler" variant="secondary" onPress={() => setEditing(false)} style={{ flex: 1 }} />
              <Button title="Enregistrer" onPress={handleSave} loading={loading} style={{ flex: 1 }} />
            </View>
          </>
        )}

        <View style={{ height: 40 }} />
      </View>
    </ScrollView>
  );
}

function InfoRow({ label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md },
  header: { alignItems: 'center', marginBottom: Spacing.lg, paddingTop: Spacing.md },
  avatar: {
    width: 80, height: 80, borderRadius: 40, backgroundColor: Colors.earth,
    alignItems: 'center', justifyContent: 'center', marginBottom: Spacing.sm,
  },
  username: { fontSize: 20, fontWeight: 'bold', color: Colors.night },
  email: { fontSize: 13, color: Colors.textMuted },
  badges: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
  verifBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: Radius.full,
    backgroundColor: Colors.borderLight,
  },
  verifOk: { backgroundColor: Colors.success + '15' },
  verifText: { fontSize: 11, color: Colors.textMuted },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: Spacing.sm },
  ratingText: { fontSize: 14, fontWeight: '600', color: Colors.night },
  sectionTitle: { fontSize: 15, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.sm },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  infoLabel: { fontSize: 13, color: Colors.textLight },
  infoValue: { fontSize: 14, fontWeight: '500', color: Colors.text },
  pickerLabel: { fontSize: 14, fontWeight: '600', color: Colors.text, marginBottom: Spacing.xs, marginTop: Spacing.sm },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs, marginBottom: Spacing.md },
  chip: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: Radius.full,
    backgroundColor: Colors.bgCard, borderWidth: 1, borderColor: Colors.border,
    fontSize: 12, color: Colors.textLight, overflow: 'hidden',
  },
  chipActive: { backgroundColor: Colors.earth, borderColor: Colors.earth, color: Colors.white },
  editActions: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
});
