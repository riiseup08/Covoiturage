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
import { useI18n } from '../i18n';

export default function ProfileScreen() {
  const { profileData, refreshProfile } = useAuth();
  const { t } = useI18n();
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
      Alert.alert(t('success'), t('profileUpdated'));
    } catch (e) {
      Alert.alert(t('error'), e.message);
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
            <VerifBadge verified={p.id_verified} label={t('id')} />
            <VerifBadge verified={p.phone_verified} label={t('phoneLabel')} />
            <VerifBadge verified={p.driver_license_verified} label={t('driverLicense')} />
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
              <Text style={styles.sectionTitle}>{t('personalInfo')}</Text>
              <InfoRow label={t('gender')} value={p.gender === 'male' ? t('male') : p.gender === 'female' ? t('female') : '—'} />
              <InfoRow label={t('phone')} value={p.phone || '—'} />
              <InfoRow label={t('whatsapp')} value={p.whatsapp_number || '—'} />
              <InfoRow label={t('bio')} value={p.bio || '—'} />
            </Card>

            <Card>
              <Text style={styles.sectionTitle}>{t('emergencyContact')}</Text>
              <InfoRow label={t('emergencyName')} value={p.emergency_contact_name || '—'} />
              <InfoRow label={t('emergencyPhone')} value={p.emergency_contact_phone || '—'} />
            </Card>

            <Card>
              <Text style={styles.sectionTitle}>{t('mobileMoney')}</Text>
              <InfoRow label={t('momoNumber')} value={p.mobile_money_number || '—'} />
              <InfoRow label={t('momoProvider')} value={p.mobile_money_provider || '—'} />
            </Card>

            <Button title={t('editProfile')} onPress={startEdit} style={{ marginTop: Spacing.sm }} />
          </>
        ) : (
          <>
            {/* Edit mode */}
            <Card>
              <Text style={styles.sectionTitle}>{`✏️ ${t('editProfileTitle')}`}</Text>
              <Input label={t('bio')} value={form.bio} onChangeText={v => update('bio', v)} multiline />
              <Input label={t('phone')} value={form.phone} onChangeText={v => update('phone', v)} keyboardType="phone-pad" />
              <Input label={t('whatsapp')} value={form.whatsapp_number} onChangeText={v => update('whatsapp_number', v)} keyboardType="phone-pad" />

              <Text style={styles.pickerLabel}>{t('gender')}</Text>
              <View style={styles.chipRow}>
                {[{ v: 'male', l: t('male') }, { v: 'female', l: t('female') }].map(g => (
                  <Text
                    key={g.v}
                    style={[styles.chip, form.gender === g.v && styles.chipActive]}
                    onPress={() => update('gender', g.v)}
                  >
                    {g.l}
                  </Text>
                ))}
              </View>

              <Input label={t('emergencyContactName')} value={form.emergency_contact_name} onChangeText={v => update('emergency_contact_name', v)} />
              <Input label={t('emergencyContactPhone')} value={form.emergency_contact_phone} onChangeText={v => update('emergency_contact_phone', v)} keyboardType="phone-pad" />
              <Input label={t('momoNumberLabel')} value={form.mobile_money_number} onChangeText={v => update('mobile_money_number', v)} keyboardType="phone-pad" />

              <Text style={styles.pickerLabel}>{t('momoProviderLabel')}</Text>
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
              <Button title={t('cancel')} variant="secondary" onPress={() => setEditing(false)} style={{ flex: 1 }} />
              <Button title={t('save')} onPress={handleSave} loading={loading} style={{ flex: 1 }} />
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
