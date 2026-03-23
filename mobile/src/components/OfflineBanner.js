import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, Radius } from '../theme';
import { useI18n } from '../i18n';

let NetInfo = null;
if (Platform.OS !== 'web') {
  try { NetInfo = require('@react-native-community/netinfo'); } catch {}
}

export default function OfflineBanner() {
  const { t } = useI18n();
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    if (Platform.OS === 'web') {
      const handleOnline = () => setIsOffline(false);
      const handleOffline = () => setIsOffline(true);
      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);
      setIsOffline(!navigator.onLine);
      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
    if (NetInfo) {
      const unsubscribe = NetInfo.default.addEventListener(state => {
        setIsOffline(!state.isConnected);
      });
      return () => unsubscribe();
    }
  }, []);

  if (!isOffline) return null;

  return (
    <View style={styles.banner}>
      <Ionicons name="cloud-offline" size={16} color={Colors.white} />
      <Text style={styles.text}>{t('offlineBanner')}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.xs,
    backgroundColor: Colors.danger,
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.md,
  },
  text: {
    color: Colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
});
