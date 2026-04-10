import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import { Colors, Spacing, Radius } from '../theme';
import Card from '../components/Card';
import Button from '../components/Button';
import { matches as matchApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';
import { fetchWithCache } from '../utils/offline';

export default function MatchesScreen({ navigation }) {
  const { user } = useAuth();
  const { t } = useI18n();
  const [list, setList] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const load = async () => {
    try {
      setLoadError(null);
      const { data } = await fetchWithCache('my_matches', () => matchApi.mine());
      setList(data);
    } catch (e) {
      setLoadError(e.message || t('loadErrorMessage'));
    }
  };

  useFocusEffect(useCallback(() => { load(); }, []));
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const handleValidate = async (id) => {
    try {
      await matchApi.validate(id);
      Alert.alert(t('success'), t('matchValidated'));
      load();
    } catch (e) { Alert.alert(t('error'), e.message); }
  };

  const handleRefuse = async (id) => {
    Alert.alert(t('confirm'), t('confirmRefuse'), [
      { text: t('no') },
      { text: t('yes'), style: 'destructive', onPress: async () => {
        try { await matchApi.refuse(id); load(); } catch (e) { Alert.alert(t('error'), e.message); }
      }},
    ]);
  };

  const renderItem = ({ item }) => {
    const isDriver = item.voyage?.conducteur_username === user?.username;
    const otherUser = isDriver ? item.demande?.passager_username : item.voyage?.conducteur_username;
    const status = item.refus_conducteur || item.refus_passager ? 'refused'
      : item.is_validated ? 'validated' : 'pending';

    return (
      <Card>
        <View style={styles.matchHeader}>
          <View style={styles.matchRoute}>
            <Text style={styles.routeText}>
              {item.voyage?.ville_depart} → {item.voyage?.ville_arrivee}
            </Text>
            <Text style={styles.matchMeta}>
              {isDriver ? `🚗 ${t('youAreDriver')}` : `🙋 ${t('youArePassenger')}`}
              {' · '}{otherUser}
            </Text>
          </View>
          <StatusBadge status={status} t={t} />
        </View>

        <View style={styles.matchDetails}>
          <Text style={styles.detailText}>Score: {Math.round(item.score_match * 100)}%</Text>
          <Text style={styles.detailText}>{item.voyage?.prix_par_place} {item.voyage?.currency}</Text>
        </View>

        {status === 'pending' && isDriver && (
          <View style={styles.actions}>
            <Button title={t('validate')} onPress={() => handleValidate(item.id)} style={{ flex: 1 }} />
            <Button title={t('refuse')} variant="danger" onPress={() => handleRefuse(item.id)} style={{ flex: 1 }} />
          </View>
        )}

        {status === 'validated' && (
          <Button
            title={`💬 ${t('conversation')}`}
            variant="secondary"
            onPress={() => navigation.navigate('Conversation', { correspondanceId: item.id })}
            style={{ marginTop: Spacing.sm }}
          />
        )}
      </Card>
    );
  };

  return (
    <FlatList
      style={styles.container}
      data={list}
      keyExtractor={item => String(item.id)}
      renderItem={renderItem}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.earth} />}
      contentContainerStyle={styles.list}
      ListEmptyComponent={
        loadError ? (
          <View style={styles.empty}>
            <Ionicons name="alert-circle-outline" size={48} color={Colors.danger} />
            <Text style={styles.emptyText}>{loadError}</Text>
          </View>
        ) : (
          <View style={styles.empty}>
            <Ionicons name="git-compare-outline" size={48} color={Colors.border} />
            <Text style={styles.emptyText}>{t('noMatchesYet')}</Text>
          </View>
        )
      }
    />
  );
}

function StatusBadge({ status, t }) {
  const config = {
    pending: { color: Colors.warning, label: t('pending'), icon: 'time' },
    validated: { color: Colors.success, label: t('validated'), icon: 'checkmark-circle' },
    refused: { color: Colors.danger, label: t('refused'), icon: 'close-circle' },
  };
  const c = config[status];
  return (
    <View style={[styles.statusBadge, { backgroundColor: c.color + '15' }]}>
      <Ionicons name={c.icon} size={12} color={c.color} />
      <Text style={[styles.statusText, { color: c.color }]}>{c.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  list: { padding: Spacing.md },
  matchHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  matchRoute: { flex: 1 },
  routeText: { fontSize: 15, fontWeight: '600', color: Colors.night },
  matchMeta: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: Radius.full },
  statusText: { fontSize: 11, fontWeight: '600' },
  matchDetails: { flexDirection: 'row', gap: Spacing.md, marginTop: Spacing.sm },
  detailText: { fontSize: 13, color: Colors.textLight },
  actions: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.md },
  empty: { alignItems: 'center', marginTop: 80 },
  emptyText: { fontSize: 15, color: Colors.textMuted, marginTop: Spacing.sm },
});
