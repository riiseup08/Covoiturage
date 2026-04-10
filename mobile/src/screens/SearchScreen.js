import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator, Platform, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
let MapView, Marker, Polyline;
if (Platform.OS !== 'web') {
  const Maps = require('react-native-maps');
  MapView = Maps.default;
  Marker = Maps.Marker;
  Polyline = Maps.Polyline;
}
import { Colors, Spacing, Radius } from '../theme';
import Input from '../components/Input';
import Button from '../components/Button';
import TripCard from '../components/TripCard';
import { voyages } from '../api/client';
import { useI18n } from '../i18n';
import { fetchWithCache } from '../utils/offline';

export default function SearchScreen({ navigation }) {
  const { t } = useI18n();
  const [villeDepart, setVilleDepart] = useState('');
  const [villeArrivee, setVilleArrivee] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [showMap, setShowMap] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const params = {};
      if (villeDepart.trim()) params.ville_depart = villeDepart.trim();
      if (villeArrivee.trim()) params.ville_arrivee = villeArrivee.trim();
      const cacheKey = `search_${villeDepart}_${villeArrivee}`;
      const { data } = await fetchWithCache(cacheKey, () => voyages.search(params));
      setResults(Array.isArray(data) ? data : data.results || []);
    } catch (e) {
      setResults([]);
      Alert.alert(t('error'), e.message || t('loadErrorMessage'));
    } finally {
      setLoading(false);
    }
  };

  const geoTrips = results.filter(t => t.start_latitude && t.end_latitude);

  const getRegion = () => {
    if (geoTrips.length === 0) return { latitude: 5.95, longitude: 10.15, latitudeDelta: 5, longitudeDelta: 5 };
    const lats = geoTrips.flatMap(t => [t.start_latitude, t.end_latitude]);
    const lons = geoTrips.flatMap(t => [t.start_longitude, t.end_longitude]);
    const minLat = Math.min(...lats), maxLat = Math.max(...lats);
    const minLon = Math.min(...lons), maxLon = Math.max(...lons);
    return {
      latitude: (minLat + maxLat) / 2,
      longitude: (minLon + maxLon) / 2,
      latitudeDelta: Math.max(maxLat - minLat, 0.5) * 1.3,
      longitudeDelta: Math.max(maxLon - minLon, 0.5) * 1.3,
    };
  };

  return (
    <View style={styles.container}>
      {/* Search bar */}
      <View style={styles.searchBox}>
        <Input placeholder={t('departureCitySearch')} value={villeDepart} onChangeText={setVilleDepart} style={styles.inputHalf} />
        <Input placeholder={t('arrivalCitySearch')} value={villeArrivee} onChangeText={setVilleArrivee} style={styles.inputHalf} />
        <Button title={t('search')} onPress={handleSearch} loading={loading} style={{ marginTop: -4 }} />
      </View>

      {/* Map toggle */}
      {Platform.OS !== 'web' && geoTrips.length > 0 && (
        <TouchableOpacity style={styles.mapToggle} onPress={() => setShowMap(!showMap)}>
          <Ionicons name={showMap ? 'list' : 'map'} size={18} color={Colors.earth} />
          <Text style={styles.mapToggleText}>{showMap ? t('viewList') : t('viewMap')}</Text>
        </TouchableOpacity>
      )}

      {/* Map */}
      {Platform.OS !== 'web' && showMap && geoTrips.length > 0 && (
        <MapView style={styles.map} initialRegion={getRegion()}>
          {geoTrips.map(t => (
            <React.Fragment key={t.id}>
              <Marker
                coordinate={{ latitude: t.start_latitude, longitude: t.start_longitude }}
                title={`D: ${t.ville_depart}`}
                description={`${t.conducteur_username} · ${t.prix_par_place} ${t.currency}`}
                pinColor="orange"
              />
              <Marker
                coordinate={{ latitude: t.end_latitude, longitude: t.end_longitude }}
                title={`A: ${t.ville_arrivee}`}
                pinColor={Colors.earth}
              />
              <Polyline
                coordinates={[
                  { latitude: t.start_latitude, longitude: t.start_longitude },
                  { latitude: t.end_latitude, longitude: t.end_longitude },
                ]}
                strokeColor={Colors.earth}
                strokeWidth={2}
                lineDashPattern={[6, 4]}
              />
            </React.Fragment>
          ))}
        </MapView>
      )}

      {/* Results list */}
      {!showMap && (
        <FlatList
          data={results}
          keyExtractor={item => String(item.id)}
          renderItem={({ item }) => (
            <TripCard trip={item} onPress={() => navigation.navigate('TripDetail', { trip: item })} />
          )}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            searched && !loading ? (
              <View style={styles.empty}>
                <Ionicons name="search-outline" size={48} color={Colors.border} />
                <Text style={styles.emptyText}>{t('noTripsFound')}</Text>
              </View>
            ) : null
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  searchBox: { padding: Spacing.md, backgroundColor: Colors.bgCard, borderBottomWidth: 1, borderBottomColor: Colors.borderLight },
  inputHalf: { marginBottom: Spacing.sm },
  mapToggle: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm,
    backgroundColor: Colors.bgCard, borderBottomWidth: 1, borderBottomColor: Colors.borderLight,
  },
  mapToggleText: { fontSize: 13, color: Colors.earth, fontWeight: '500' },
  map: { height: 300 },
  list: { padding: Spacing.md },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 15, color: Colors.textMuted, marginTop: Spacing.sm },
});
