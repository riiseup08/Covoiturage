import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Image,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';
import { formatCurrency } from '../utils/currency';
import { payments } from '../api/client';

/**
 * Transaction Confirmation Screen - Crystal clear payment breakdown
 * Shows EXACTLY:
 * - Who is paying (passenger)
 * - Who is receiving (driver)
 * - What they're paying for (trip fare)
 * - When money moves (immediate for cash, on completion for MoMo)
 * - Confirmation action
 */
export default function TransactionConfirmationScreen({ route, navigation }) {
  const { t } = useI18n();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [visualMode] = useState('clear'); // Show maximum clarity

  const {
    correspondance,
    voyage,
    demande,
    method, // 'mobile_money' or 'cash'
    provider, // 'mtn', 'orange', etc
    amount,
  } = route.params;

  const isPassenger = user.id === demande.passager;
  const passenger = demande; // Has passager object
  const driver = voyage.conducteur_username; // Driver username
  const tripFrom = voyage.ville_depart;
  const tripTo = voyage.ville_arrivee;

  const handleConfirmPayment = async () => {
    setLoading(true);
    try {
      Alert.alert(
        t('confirmPayment'),
        `💰 ${t('paying')} ${formatCurrency(amount, 'XAF')}\n\n${tripFrom} → ${tripTo}\n\n${method === 'cash' ? t('cashPaymentLabel') : provider}`,
        [
          { text: t('cancel'), onPress: () => setLoading(false) },
          {
            text: t('confirm'),
            onPress: async () => {
              try {
                await payments.create({
                  correspondance_id: correspondance.id,
                  method,
                  provider: method === 'mobile_money' ? provider : 'cash',
                  amount,
                });
                Alert.alert(
                  t('success'),
                  t('paymentSuccess')
                );
                setTimeout(() => navigation.goBack(), 1500);
              } catch (err) {
                setLoading(false);
                Alert.alert(t('error'), err.message || t('actionFailed'));
              }
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert(t('error'), error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header: Title + Status */}
      <View style={styles.header}>
        <MaterialCommunityIcons name="check-circle-outline" size={48} color="#34C759" />
        <Text style={styles.headerTitle}>{t('reviewTransaction')}</Text>
        <Text style={styles.headerSubtitle}>{t('ensureDetailsCorrect')}</Text>
      </View>

      {/* SECTION 1: TRIP DETAILS */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>{t('tripDetailsSection')}</Text>
        <View style={styles.tripCard}>
          <View style={styles.tripRoute}>
            <View style={styles.routePoint}>
              <MaterialCommunityIcons name="map-marker" size={24} color="#007AFF" />
              <Text style={styles.routeText}>{tripFrom}</Text>
            </View>
            <View style={styles.routeLine} />
            <View style={styles.routePoint}>
              <MaterialCommunityIcons name="flag-checkered" size={24} color="#34C759" />
              <Text style={styles.routeText}>{tripTo}</Text>
            </View>
          </View>

          <View style={styles.tripMeta}>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>{t('date')}</Text>
              <Text style={styles.metaValue}>{new Date(voyage.date_depart).toLocaleDateString('fr-FR')}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>{t('seats')}</Text>
              <Text style={styles.metaValue}>{demande.places} {t('places')}</Text>
            </View>
          </View>
        </View>
      </View>

      {/* SECTION 2: PEOPLE INVOLVED */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>{t('paymentFlowSection')}</Text>

        {/* PASSENGER (YOU) - PAYING */}
        <View style={[styles.personCard, styles.passengerCard]}>
          <View style={styles.personHeader}>
            <View style={styles.roleIcon}>
              <MaterialCommunityIcons name="account" size={20} color="#FFF" />
            </View>
            <View style={styles.personInfo}>
              <Text style={styles.personLabel}>{t('youPassenger')}</Text>
              <Text style={styles.personName}>{t('payingTrip')}</Text>
            </View>
          </View>
          <View style={styles.personAction}>
            <MaterialCommunityIcons name="cash-remove" size={32} color="#FF3B30" />
            <Text style={styles.actionText}>{t('paying')} {formatCurrency(amount, 'XAF')}</Text>
          </View>
        </View>

        {/* Arrow */}
        <View style={styles.arrowContainer}>
          <MaterialCommunityIcons name="arrow-down" size={32} color="#999" />
          <Text style={styles.arrowLabel}>{method === 'cash' ? t('cashPaymentLabel') : t('mobileMoneyLabel')}</Text>
        </View>

        {/* DRIVER (RECEIVER) - RECEIVING */}
        <View style={[styles.personCard, styles.driverCard]}>
          <View style={styles.personHeader}>
            <View style={styles.roleIconDriver}>
              <MaterialCommunityIcons name="steering" size={20} color="#FFF" />
            </View>
            <View style={styles.personInfo}>
              <Text style={styles.personLabel}>{t('driverLabel')}</Text>
              <Text style={styles.personName}>{driver}</Text>
            </View>
          </View>
          <View style={styles.personAction}>
            <MaterialCommunityIcons name="cash-check" size={32} color="#34C759" />
            <Text style={styles.actionText}>{t('receives')} {formatCurrency(amount, 'XAF')}</Text>
          </View>
        </View>
      </View>

      {/* SECTION 3: PAYMENT METHOD */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>💳 PAYMENT METHOD</Text>
        <View style={styles.paymentMethodCard}>
          <View style={styles.methodRow}>
            <Text style={styles.methodLabel}>Method:</Text>
            <Text style={styles.methodValue}>
              {method === 'cash' ? `💵 ${t('cashPaymentLabel')}` : `📱 ${t('mobileMoneyLabel')}`}
            </Text>
          </View>
          {method === 'mobile_money' && (
            <View style={styles.methodRow}>
              <Text style={styles.methodLabel}>Provider:</Text>
              <Text style={styles.methodValue}>{provider.toUpperCase()}</Text>
            </View>
          )}
          <View style={styles.methodRow}>
            <Text style={styles.methodLabel}>Amount:</Text>
            <Text style={styles.methodValue}>{formatCurrency(amount, 'XAF')}</Text>
          </View>
          <View style={styles.methodRow}>
            <Text style={styles.methodLabel}>Status:</Text>
            <Text style={[styles.methodValue, { color: method === 'cash' ? '#34C759' : '#9999FF' }]}>
              {method === 'cash' ? '✓ Immediate' : 'Pending'}
            </Text>
          </View>
        </View>
      </View>

      {/* SECTION 4: IMPORTANT NOTES */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>ℹ️ IMPORTANT</Text>
        <View style={styles.noteBox}>
          <Text style={styles.noteTitle}>Payment Timing:</Text>
          <Text style={styles.noteText}>
            {method === 'cash'
              ? '💵 Cash is paid directly to the driver during the trip. Make sure you have exact change!'
              : '📱 Mobile Money payment will be processed via ' +
                provider.toUpperCase() +
                '. You will receive a confirmation.'}
          </Text>
        </View>

        <View style={[styles.noteBox, styles.noteBoxWarning]}>
          <Text style={styles.noteTitle}>Before confirming:</Text>
          <Text style={styles.noteText}>✓ {t('ensureDetailsCorrect')} ✓ {formatCurrency(amount, 'XAF')}</Text>
        </View>
      </View>

      {/* ACTION BUTTONS */}
      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => navigation.goBack()}
          disabled={loading}
        >
          <Text style={styles.cancelButtonText}>{t('cancel')}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.confirmButton}
          onPress={handleConfirmPayment}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#FFF" />
          ) : (
            <>
              <MaterialCommunityIcons name="check" size={20} color="#FFF" />
              <Text style={styles.confirmButtonText}>{t('confirm')} {formatCurrency(amount, 'XAF')}</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9F9F9',
  },
  header: {
    backgroundColor: '#FFF',
    paddingVertical: 24,
    paddingHorizontal: 16,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#222',
    marginTop: 12,
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#999',
    marginTop: 4,
  },
  section: {
    backgroundColor: '#FFF',
    marginVertical: 8,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#666',
    marginBottom: 12,
    letterSpacing: 0.5,
  },
  tripCard: {
    backgroundColor: '#F5F7FF',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  tripRoute: {
    marginBottom: 16,
  },
  routePoint: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 8,
  },
  routeText: {
    marginLeft: 12,
    fontSize: 14,
    fontWeight: '600',
    color: '#222',
    flex: 1,
  },
  routeLine: {
    height: 24,
    borderLeftWidth: 2,
    borderLeftColor: '#CCC',
    marginLeft: 10,
  },
  tripMeta: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#DDD',
  },
  metaItem: {
    alignItems: 'center',
  },
  metaLabel: {
    fontSize: 11,
    color: '#999',
    fontWeight: '500',
  },
  metaValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#222',
    marginTop: 4,
  },
  personCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    backgroundColor: '#F5F5F5',
  },
  passengerCard: {
    backgroundColor: '#FFF4F4',
    borderLeftWidth: 4,
    borderLeftColor: '#FF3B30',
  },
  driverCard: {
    backgroundColor: '#F4FFF5',
    borderLeftWidth: 4,
    borderLeftColor: '#34C759',
  },
  personHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  roleIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FF3B30',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  roleIconDriver: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  personInfo: {
    flex: 1,
  },
  personLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#666',
    letterSpacing: 0.5,
  },
  personName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222',
    marginTop: 2,
  },
  personAction: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#DDD',
  },
  actionText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#222',
    marginLeft: 12,
  },
  arrowContainer: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  arrowLabel: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
    fontWeight: '600',
  },
  paymentMethodCard: {
    backgroundColor: '#F9F9F9',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  methodRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E8E8E8',
  },
  methodRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  methodLabel: {
    fontSize: 13,
    color: '#666',
    fontWeight: '500',
  },
  methodValue: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#222',
  },
  noteBox: {
    backgroundColor: '#E8F5E9',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  noteBoxWarning: {
    backgroundColor: '#FFF3E0',
    borderLeftColor: '#FF9800',
  },
  noteTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#222',
  },
  noteText: {
    fontSize: 12,
    color: '#555',
    marginTop: 6,
    lineHeight: 18,
  },
  actionButtons: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 16,
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222',
  },
  confirmButton: {
    flex: 1.5,
    backgroundColor: '#34C759',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  confirmButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFF',
    marginLeft: 6,
  },
});
