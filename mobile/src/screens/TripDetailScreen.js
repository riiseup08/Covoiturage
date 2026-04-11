import React from 'react';
import { View, Text, StyleSheet, ScrollView, Platform, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
let MapView, Marker, Polyline;
if (Platform.OS !== 'web') {
  const Maps = require('react-native-maps');
  MapView = Maps.default;
  Marker = Maps.Marker;
  Polyline = Maps.Polyline;
}
import { Colors, Spacing, Radius } from '../theme';
import Card from '../components/Card';
import Button from '../components/Button';
import { useI18n } from '../i18n';
import { formatCurrency } from '../utils/currency';

export default function TripDetailScreen({ route, navigation }) {
  const { trip } = route.params;
  const { t } = useI18n();

  const formatDate = (d) => new Date(d).toLocaleDateString('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

  const hasGeo = trip.start_latitude && trip.end_latitude;

  return (
    <ScrollView style={styles.container}>
      {/* Map */}
      {Platform.OS !== 'web' && hasGeo && (
        <MapView
          style={styles.map}
          initialRegion={{
            latitude: (trip.start_latitude + trip.end_latitude) / 2,
            longitude: (trip.start_longitude + trip.end_longitude) / 2,
            latitudeDelta: Math.abs(trip.start_latitude - trip.end_latitude) * 1.5 || 0.5,
            longitudeDelta: Math.abs(trip.start_longitude - trip.end_longitude) * 1.5 || 0.5,
          }}
        >
          <Marker coordinate={{ latitude: trip.start_latitude, longitude: trip.start_longitude }} title={trip.ville_depart} pinColor="orange" />
          <Marker coordinate={{ latitude: trip.end_latitude, longitude: trip.end_longitude }} title={trip.ville_arrivee} pinColor={Colors.earth} />
          <Polyline
            coordinates={[
              { latitude: trip.start_latitude, longitude: trip.start_longitude },
              { latitude: trip.end_latitude, longitude: trip.end_longitude },
            ]}
            strokeColor={Colors.earth}
            strokeWidth={3}
            lineDashPattern={[8, 4]}
          />
        </MapView>
      )}

      <View style={styles.content}>
        {/* Route */}
        <Card>
          <View style={styles.routeRow}>
            <View style={styles.routeDots}>
              <View style={[styles.dot, { backgroundColor: Colors.sun }]} />
              <View style={styles.line} />
              <View style={[styles.dot, { backgroundColor: Colors.earth }]} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.city}>{trip.ville_depart}</Text>
              {trip.lieu_ramassage ? <Text style={styles.pickup}>📍 {trip.lieu_ramassage}</Text> : null}
              <View style={{ height: 12 }} />
              <Text style={styles.city}>{trip.ville_arrivee}</Text>
            </View>
          </View>
        </Card>

        {/* Details */}
        <Card>
          <Text style={styles.sectionTitle}>{t('tripDetails')}</Text>
          <DetailRow icon="calendar-outline" label={t('departureLabel')} value={formatDate(trip.date_depart)} />
          <DetailRow icon="time-outline" label={t('arrivalLabel')} value={formatDate(trip.date_arrivee)} />
          <DetailRow icon="people-outline" label={t('seats')} value={`${trip.places_disponibles}`} />
          <DetailRow icon="pricetag-outline" label={t('pricePerSeatLabel')} value={formatCurrency(trip.prix_par_place, trip.currency)} />
          <DetailRow icon="briefcase-outline" label={t('baggage')} value={trip.type_bagage_accepte} />
          {trip.women_only && <DetailRow icon="female" label={t('reservedForWomen')} value="Oui" color={Colors.female} />}
        </Card>

        {/* Vehicle */}
        {(trip.modele_voiture || trip.plaque_immatriculation) && (
          <Card>
            <Text style={styles.sectionTitle}>{`🚗 ${t('vehicleSection')}`}</Text>
            {trip.modele_voiture && <DetailRow icon="car-outline" label={t('model')} value={trip.modele_voiture} />}
            {trip.plaque_immatriculation && <DetailRow icon="document-text-outline" label={t('plate')} value={trip.plaque_immatriculation} />}
          </Card>
        )}

        {/* Payment */}
        <Card>
          <Text style={styles.sectionTitle}>{`💳 ${t('paymentSection')}`}</Text>
          {trip.accept_mobile_money && <DetailRow icon="phone-portrait-outline" label={t('payByMoMo')} value={t('accepted')} color={Colors.success} />}
          {trip.accept_cash && <DetailRow icon="cash-outline" label={t('payByCash')} value={t('accepted')} color={Colors.success} />}
        </Card>

        {/* Driver */}
        <Card>
          <Text style={styles.sectionTitle}>{t('driverSection')}</Text>
          <TouchableRow
            icon="person-circle-outline"
            label={trip.conducteur_username}
            onPress={() => navigation.navigate('PublicProfile', { username: trip.conducteur_username })}
          />
        </Card>

        <View style={{ height: 30 }} />
      </View>
    </ScrollView>
  );
}

function DetailRow({ icon, label, value, color }) {
  return (
    <View style={styles.detailRow}>
      <Ionicons name={icon} size={18} color={color || Colors.earth} />
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

function TouchableRow({ icon, label, onPress }) {
  return (
    <Text style={styles.touchableRow} onPress={onPress}>
      <Ionicons name={icon} size={18} color={Colors.earth} /> {label} →
    </Text>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  map: { height: 200 },
  content: { padding: Spacing.md },
  routeRow: { flexDirection: 'row' },
  routeDots: { alignItems: 'center', marginRight: Spacing.md },
  dot: { width: 12, height: 12, borderRadius: 6 },
  line: { width: 2, height: 20, backgroundColor: Colors.border },
  city: { fontSize: 17, fontWeight: 'bold', color: Colors.night },
  pickup: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
  sectionTitle: { fontSize: 15, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.sm },
  detailRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6, gap: Spacing.sm },
  detailLabel: { flex: 1, fontSize: 13, color: Colors.textLight },
  detailValue: { fontSize: 14, fontWeight: '600', color: Colors.text },
  touchableRow: { fontSize: 15, color: Colors.earth, fontWeight: '500', paddingVertical: 4 },
});
