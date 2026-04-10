import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import { Colors, Spacing, Radius } from '../theme';
import Button from '../components/Button';
import { notifications as notifApi } from '../api/client';
import { useI18n } from '../i18n';
import { fetchWithCache } from '../utils/offline';

export default function NotificationsScreen() {
  const { t } = useI18n();
  const [data, setData] = useState({ notifications: [], unread_count: 0 });
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const load = async () => {
    try {
      setLoadError(null);
      const { data: d } = await fetchWithCache('notifications', () => notifApi.list());
      setData(d);
    } catch (e) {
      setLoadError(e.message || t('loadErrorMessage'));
    }
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const markRead = async (id) => {
    try {
      await notifApi.markRead(id);
      setData(prev => ({
        ...prev,
        unread_count: Math.max(0, prev.unread_count - 1),
        notifications: prev.notifications.map(n => n.id === id ? { ...n, is_read: true } : n),
      }));
    } catch (e) {
      Alert.alert(t('error'), e.message || t('actionFailed'));
    }
  };

  const markAllRead = async () => {
    try {
      await notifApi.markAllRead();
      setData(prev => ({
        ...prev,
        unread_count: 0,
        notifications: prev.notifications.map(n => ({ ...n, is_read: true })),
      }));
    } catch (e) {
      Alert.alert(t('error'), e.message || t('actionFailed'));
    }
  };

  const formatDate = (d) => {
    const date = new Date(d);
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return t('justNow');
    if (diff < 3600000) return `${t('ago')} ${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return `${t('ago')} ${Math.floor(diff / 3600000)}h`;
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={[styles.notifItem, !item.is_read && styles.notifUnread]}
      onPress={() => !item.is_read && markRead(item.id)}
      activeOpacity={0.7}
    >
      <Text style={styles.notifIcon}>{item.icon}</Text>
      <View style={styles.notifContent}>
        <Text style={[styles.notifTitle, !item.is_read && { fontWeight: 'bold' }]}>{item.title}</Text>
        <Text style={styles.notifMessage} numberOfLines={2}>{item.message}</Text>
        <Text style={styles.notifTime}>{formatDate(item.created_at)}</Text>
      </View>
      {!item.is_read && <View style={styles.unreadDot} />}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {data.unread_count > 0 && (
        <View style={styles.topBar}>
          <Text style={styles.unreadCount}>{data.unread_count} {t('unreadLabel')}</Text>
          <TouchableOpacity onPress={markAllRead}>
            <Text style={styles.markAllLink}>{t('markAllRead')}</Text>
          </TouchableOpacity>
        </View>
      )}

      <FlatList
        data={data.notifications}
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
            <Ionicons name="notifications-off-outline" size={48} color={Colors.border} />
            <Text style={styles.emptyText}>{t('noNotifications')}</Text>
          </View>
        )
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  topBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm,
    backgroundColor: Colors.bgCard, borderBottomWidth: 1, borderBottomColor: Colors.borderLight,
  },
  unreadCount: { fontSize: 13, fontWeight: '600', color: Colors.earth },
  markAllLink: { fontSize: 13, color: Colors.sun, fontWeight: '500' },
  list: { paddingBottom: Spacing.lg },
  notifItem: {
    flexDirection: 'row', alignItems: 'center', padding: Spacing.md,
    borderBottomWidth: 1, borderBottomColor: Colors.borderLight,
    backgroundColor: Colors.bgCard,
  },
  notifUnread: { backgroundColor: Colors.earth + '08' },
  notifIcon: { fontSize: 24, marginRight: Spacing.sm },
  notifContent: { flex: 1 },
  notifTitle: { fontSize: 14, color: Colors.night },
  notifMessage: { fontSize: 12, color: Colors.textLight, marginTop: 2 },
  notifTime: { fontSize: 11, color: Colors.textMuted, marginTop: 4 },
  unreadDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.sun, marginLeft: Spacing.sm },
  empty: { alignItems: 'center', marginTop: 80 },
  emptyText: { fontSize: 15, color: Colors.textMuted, marginTop: Spacing.sm },
});
