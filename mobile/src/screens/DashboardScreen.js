import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import { Colors, Spacing, Radius } from '../theme';
import Card from '../components/Card';
import { dashboard, voyages, demandes } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function DashboardScreen({ navigation }) {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [myTrips, setMyTrips] = useState([]);
  const [myDemandes, setMyDemandes] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const [s, t, d] = await Promise.all([dashboard.stats(), voyages.mine(), demandes.mine()]);
      setStats(s);
      setMyTrips(t.slice(0, 3));
      setMyDemandes(d.slice(0, 3));
    } catch { /* ignore */ }
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const StatBox = ({ icon, label, value, color }) => (
    <View style={styles.statBox}>
      <Ionicons name={icon} size={24} color={color || Colors.earth} />
      <Text style={styles.statValue}>{value ?? '—'}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );

  const formatDate = (d) => new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.earth} />}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Bonjour 👋</Text>
          <Text style={styles.username}>{user?.username}</Text>
        </View>
        <TouchableOpacity onPress={logout} style={styles.logoutBtn}>
          <Ionicons name="log-out-outline" size={22} color={Colors.danger} />
        </TouchableOpacity>
      </View>

      {/* Stats grid */}
      {stats && (
        <View style={styles.statsGrid}>
          <StatBox icon="car" label="Mes trajets" value={stats.voyages_count} />
          <StatBox icon="hand-left" label="Demandes" value={stats.demandes_count} />
          <StatBox icon="checkmark-circle" label="Matchs validés" value={stats.validated_matches_count} color={Colors.success} />
          <StatBox icon="star" label="Note moyenne" value={stats.avg_rating || '—'} color={Colors.star} />
          <StatBox icon="flag" label="Terminés (conducteur)" value={stats.completed_as_driver} color={Colors.sun} />
          <StatBox icon="person" label="Terminés (passager)" value={stats.completed_as_passenger} color={Colors.earthLight} />
        </View>
      )}

      {/* Quick actions */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('AddTrip')}>
          <Ionicons name="add-circle" size={20} color={Colors.white} />
          <Text style={styles.actionText}>Publier un trajet</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, styles.actionSecondary]} onPress={() => navigation.navigate('AddDemande')}>
          <Ionicons name="search" size={20} color={Colors.earth} />
          <Text style={[styles.actionText, { color: Colors.earth }]}>Poster une demande</Text>
        </TouchableOpacity>
      </View>

      {/* Recent trips */}
      {myTrips.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Mes derniers trajets</Text>
          {myTrips.map(t => (
            <Card key={t.id} style={styles.miniCard}>
              <Text style={styles.miniRoute}>{t.ville_depart} → {t.ville_arrivee}</Text>
              <Text style={styles.miniDate}>{formatDate(t.date_depart)} · {t.prix_par_place} {t.currency}</Text>
            </Card>
          ))}
        </View>
      )}

      {/* Notification badge */}
      {stats && stats.unread_notifications > 0 && (
        <TouchableOpacity style={styles.notifBanner} onPress={() => navigation.navigate('NotificationsTab')}>
          <Ionicons name="notifications" size={18} color={Colors.sun} />
          <Text style={styles.notifText}>{stats.unread_notifications} notification(s) non lue(s)</Text>
        </TouchableOpacity>
      )}

      <View style={{ height: 30 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: Spacing.lg, paddingTop: Spacing.xl },
  greeting: { fontSize: 14, color: Colors.textLight },
  username: { fontSize: 22, fontWeight: 'bold', color: Colors.night },
  logoutBtn: { padding: Spacing.sm },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: Spacing.md, gap: Spacing.sm },
  statBox: {
    width: '31%', backgroundColor: Colors.bgCard, borderRadius: Radius.md, padding: Spacing.md,
    alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
  },
  statValue: { fontSize: 20, fontWeight: 'bold', color: Colors.night, marginTop: Spacing.xs },
  statLabel: { fontSize: 10, color: Colors.textMuted, textAlign: 'center', marginTop: 2 },
  actions: { flexDirection: 'row', paddingHorizontal: Spacing.md, gap: Spacing.sm, marginTop: Spacing.lg },
  actionBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    backgroundColor: Colors.earth, paddingVertical: Spacing.md, borderRadius: Radius.md,
  },
  actionSecondary: { backgroundColor: Colors.bgCard, borderWidth: 1.5, borderColor: Colors.earth },
  actionText: { fontSize: 13, fontWeight: '600', color: Colors.white },
  section: { marginTop: Spacing.lg, paddingHorizontal: Spacing.md },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.sm },
  miniCard: { padding: Spacing.sm },
  miniRoute: { fontSize: 14, fontWeight: '600', color: Colors.earth },
  miniDate: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
  notifBanner: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.sm,
    margin: Spacing.md, padding: Spacing.md, backgroundColor: Colors.sun + '15',
    borderRadius: Radius.md, borderLeftWidth: 3, borderLeftColor: Colors.sun,
  },
  notifText: { fontSize: 13, color: Colors.night, fontWeight: '500' },
});
