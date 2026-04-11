import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, Radius } from '../theme';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import { payments } from '../api/client';
import { useI18n } from '../i18n';
import { formatCurrency } from '../utils/currency';

export default function PaymentScreen({ route, navigation }) {
  const { t } = useI18n();
  const { match } = route.params || {};
  const voyage = match?.voyage || {};

  const totalAmount = (parseFloat(voyage.prix_par_place) || 0) * (match?.demande?.places || 1);
  const currency = voyage.currency || 'XAF';

  const [method, setMethod] = useState('mobile_money');
  const [provider, setProvider] = useState('mtn');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const providers = [
    { id: 'mtn', label: 'MTN MoMo', icon: '🟡' },
    { id: 'orange', label: 'Orange Money', icon: '🟠' },
    { id: 'moov', label: 'Moov Money', icon: '🔵' },
    { id: 'airtel', label: 'Airtel Money', icon: '🔴' },
    { id: 'wave', label: 'Wave', icon: '🌊' },
  ];

  const handlePay = async () => {
    if (method === 'mobile_money' && !phoneNumber.trim()) {
      setError(t('phoneInvalid'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      await payments.create({
        correspondance_id: match.id,
        method,
        provider: method === 'mobile_money' ? provider : 'cash',
        phone_number: method === 'mobile_money' ? phoneNumber.trim() : '',
      });
      Alert.alert(t('success'), t('paymentSuccess'), [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (e) {
      setError(e.message || t('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Trip summary */}
        <Card>
          <Text style={styles.sectionTitle}>🚗 {voyage.ville_depart} → {voyage.ville_arrivee}</Text>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>{t('driver')}</Text>
            <Text style={styles.infoValue}>{voyage.conducteur_username}</Text>
          </View>
          <View style={styles.amountRow}>
            <Text style={styles.amountLabel}>{t('totalToPay')}</Text>
            <Text style={styles.amountValue}>{formatCurrency(totalAmount, currency)}</Text>
          </View>
        </Card>

        {/* Payment method */}
        <Card>
          <Text style={styles.sectionTitle}>{t('paymentMethod')}</Text>
          <View style={styles.methodRow}>
            <MethodButton
              active={method === 'mobile_money'}
              label={t('payByMoMo')}
              icon="phone-portrait"
              onPress={() => setMethod('mobile_money')}
              disabled={!voyage.accept_mobile_money}
            />
            <MethodButton
              active={method === 'cash'}
              label={t('payByCash')}
              icon="cash"
              onPress={() => setMethod('cash')}
              disabled={!voyage.accept_cash}
            />
          </View>
        </Card>

        {/* Mobile Money details */}
        {method === 'mobile_money' && (
          <Card>
            <Text style={styles.sectionTitle}>{t('paymentProvider')}</Text>
            <View style={styles.providerRow}>
              {providers.map(p => (
                <Text
                  key={p.id}
                  style={[styles.providerChip, provider === p.id && styles.providerActive]}
                  onPress={() => setProvider(p.id)}
                >
                  {p.icon} {p.label}
                </Text>
              ))}
            </View>

            <Input
              label={t('paymentPhone')}
              placeholder="6XX XX XX XX"
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              keyboardType="phone-pad"
            />
          </Card>
        )}

        {method === 'cash' && (
          <Card>
            <View style={styles.cashInfo}>
              <Ionicons name="information-circle" size={20} color={Colors.sun} />
              <Text style={styles.cashText}>
                {t('cashPaymentInfo')}
              </Text>
            </View>
          </Card>
        )}

        {error ? <Text style={styles.errorText}>{error}</Text> : null}

        <Button title={`${t('payNow')} - ${formatCurrency(totalAmount, currency)}`} onPress={handlePay} loading={loading} />

        <View style={{ height: 30 }} />
      </View>
    </ScrollView>
  );
}

function MethodButton({ active, label, icon, onPress, disabled }) {
  return (
    <Text
      style={[
        styles.methodBtn,
        active && styles.methodActive,
        disabled && styles.methodDisabled,
      ]}
      onPress={disabled ? undefined : onPress}
    >
      <Ionicons name={icon} size={16} /> {label}
    </Text>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md },
  sectionTitle: { fontSize: 15, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.sm },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  infoLabel: { fontSize: 13, color: Colors.textLight },
  infoValue: { fontSize: 14, fontWeight: '500', color: Colors.text },
  amountRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginTop: Spacing.sm, paddingTop: Spacing.sm,
    borderTopWidth: 1, borderTopColor: Colors.borderLight,
  },
  amountLabel: { fontSize: 15, fontWeight: '600', color: Colors.night },
  amountValue: { fontSize: 20, fontWeight: 'bold', color: Colors.earth },
  methodRow: { flexDirection: 'row', gap: Spacing.sm },
  methodBtn: {
    flex: 1, textAlign: 'center',
    paddingVertical: Spacing.md, borderRadius: Radius.md,
    borderWidth: 1.5, borderColor: Colors.border,
    backgroundColor: Colors.bgCard, color: Colors.textLight,
    fontSize: 13, fontWeight: '500', overflow: 'hidden',
  },
  methodActive: {
    borderColor: Colors.earth, backgroundColor: Colors.earth + '10',
    color: Colors.earth, fontWeight: '700',
  },
  methodDisabled: { opacity: 0.4 },
  providerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs, marginBottom: Spacing.md },
  providerChip: {
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: Radius.full,
    backgroundColor: Colors.bgCard, borderWidth: 1, borderColor: Colors.border,
    fontSize: 12, color: Colors.textLight, overflow: 'hidden',
  },
  providerActive: { backgroundColor: Colors.earth, borderColor: Colors.earth, color: Colors.white },
  cashInfo: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.sm,
    backgroundColor: Colors.sun + '10', padding: Spacing.md, borderRadius: Radius.md,
  },
  cashText: { flex: 1, fontSize: 13, color: Colors.text },
  errorText: {
    backgroundColor: Colors.danger + '15',
    color: Colors.danger,
    padding: Spacing.sm,
    borderRadius: Radius.sm,
    marginBottom: Spacing.md,
    fontSize: 13,
    textAlign: 'center',
  },
});
