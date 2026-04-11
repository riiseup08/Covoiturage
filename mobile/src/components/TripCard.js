import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Radius, Spacing } from '../theme';
import Card from './Card';
import { useI18n } from '../i18n';
import { formatCurrency, currencyLabel } from '../utils/currency';

/**
 * @typedef {object} Trip
 * @property {number} id
 * @property {string} ville_depart
 * @property {string} ville_arrivee
 * @property {number} prix_par_place
 * @property {string} currency
 * @property {string} date_depart
 * @property {number} places_disponibles
 * @property {boolean} [women_only]
 * @property {string} [conducteur_username]
 * @property {string} [modele_voiture]
 * @property {boolean} [accept_mobile_money]
 * @property {boolean} [accept_cash]
 */

/**
 * @param {object} props
 * @param {Trip} props.trip - Trip data object
 * @param {() => void} [props.onPress] - Press handler
 * @param {boolean} [props.showDriver=true] - Show driver info row
 */
export default function TripCard({ trip, onPress, showDriver = true }) {
  const { t } = useI18n();
  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      accessibilityRole="button"
      accessibilityLabel={`${trip.ville_depart} → ${trip.ville_arrivee}, ${trip.prix_par_place} ${trip.currency}`}
    >
      <Card>
        <View style={styles.route}>
          <View style={styles.routeDots}>
            <View style={[styles.dot, { backgroundColor: Colors.sun }]} />
            <View style={styles.line} />
            <View style={[styles.dot, { backgroundColor: Colors.earth }]} />
          </View>
          <View style={styles.routeText}>
            <Text style={styles.city}>{trip.ville_depart}</Text>
            <Text style={styles.city}>{trip.ville_arrivee}</Text>
          </View>
          <View style={styles.priceBox}>
            <Text style={styles.price}>{formatCurrency(trip.prix_par_place, trip.currency)}</Text>
            <Text style={styles.currency}>{currencyLabel(trip.currency)}</Text>
          </View>
        </View>

        <View style={styles.details}>
          <View style={styles.detailItem}>
            <Ionicons name="calendar-outline" size={14} color={Colors.textLight} />
            <Text style={styles.detailText}>{formatDate(trip.date_depart)}</Text>
          </View>
          <View style={styles.detailItem}>
            <Ionicons name="person-outline" size={14} color={Colors.textLight} />
            <Text style={styles.detailText}>{trip.places_disponibles} {t('places')}</Text>
          </View>
          {trip.women_only && (
            <View style={[styles.badge, { backgroundColor: Colors.female + '20' }]}>
              <Text style={[styles.badgeText, { color: Colors.female }]}>👩 {t('womenOnly')}</Text>
            </View>
          )}
        </View>

        {showDriver && trip.conducteur_username && (
          <View style={styles.driver}>
            <Ionicons name="car-outline" size={14} color={Colors.earth} />
            <Text style={styles.driverText}>{trip.conducteur_username}</Text>
            {trip.modele_voiture ? <Text style={styles.carText}> · {trip.modele_voiture}</Text> : null}
          </View>
        )}

        <View style={styles.paymentRow}>
          {trip.accept_mobile_money && (
            <View style={styles.payBadge}>
              <Text style={styles.payText}>📱 {t('mobileMoneyLabel')}</Text>
            </View>
          )}
          {trip.accept_cash && (
            <View style={styles.payBadge}>
              <Text style={styles.payText}>💵 {t('payByCash')}</Text>
            </View>
          )}
        </View>
      </Card>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  route: { flexDirection: 'row', alignItems: 'center', marginBottom: Spacing.sm },
  routeDots: { alignItems: 'center', marginRight: Spacing.sm },
  dot: { width: 10, height: 10, borderRadius: 5 },
  line: { width: 2, height: 24, backgroundColor: Colors.border, marginVertical: 2 },
  routeText: { flex: 1, justifyContent: 'space-between', height: 48 },
  city: { fontSize: 15, fontWeight: '600', color: Colors.night },
  priceBox: { alignItems: 'flex-end' },
  price: { fontSize: 18, fontWeight: 'bold', color: Colors.earth },
  currency: { fontSize: 11, color: Colors.textMuted },
  details: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, marginBottom: Spacing.sm },
  detailItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  detailText: { fontSize: 12, color: Colors.textLight },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: Radius.sm },
  badgeText: { fontSize: 11, fontWeight: '600' },
  driver: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: Spacing.xs },
  driverText: { fontSize: 13, fontWeight: '500', color: Colors.earth },
  carText: { fontSize: 12, color: Colors.textMuted },
  paymentRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.xs },
  payBadge: { backgroundColor: Colors.borderLight, paddingHorizontal: 8, paddingVertical: 3, borderRadius: Radius.sm },
  payText: { fontSize: 11, color: Colors.textLight },
});
