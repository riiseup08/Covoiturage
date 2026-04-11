import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, Radius } from '../theme';
import Card from '../components/Card';
import { profile as profileApi } from '../api/client';
import { useI18n } from '../i18n';

export default function PublicProfileScreen({ route }) {
  const { username } = route.params;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const { t } = useI18n();

  useEffect(() => {
    (async () => {
      try {
        const p = await profileApi.public(username);
        setData(p);
      } catch (e) {
        setLoadError(e.message || t('loadErrorMessage'));
      }
      setLoading(false);
    })();
  }, [username]);

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={Colors.earth} /></View>;
  if (!data) return <View style={styles.center}><Text>{loadError || t('profileNotFound')}</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={40} color={Colors.white} />
          </View>
          <Text style={styles.username}>{data.username}</Text>
          {data.avg_rating && (
            <View style={styles.ratingRow}>
              <Ionicons name="star" size={16} color={Colors.star} />
              <Text style={styles.ratingText}>{data.avg_rating}/5</Text>
            </View>
          )}
          <View style={styles.badges}>
            {data.id_verified && <Badge label={t('idVerified')} color={Colors.success} />}
            {data.phone_verified && <Badge label={t('phoneVerified')} color={Colors.success} />}
          </View>
        </View>

        {data.bio ? (
          <Card>
            <Text style={styles.bio}>{data.bio}</Text>
          </Card>
        ) : null}

        {/* Reviews */}
        {data.reviews && data.reviews.length > 0 && (
          <View>
            <Text style={styles.sectionTitle}>{t('receivedReviews')}</Text>
            {data.reviews.map(r => (
              <Card key={r.id}>
                <View style={styles.reviewHeader}>
                  <Text style={styles.reviewAuthor}>{r.auteur_username}</Text>
                  <View style={styles.stars}>
                    {[1, 2, 3, 4, 5].map(i => (
                      <Ionicons key={i} name={i <= r.note ? 'star' : 'star-outline'} size={14} color={Colors.star} />
                    ))}
                  </View>
                </View>
                {r.commentaire ? <Text style={styles.reviewComment}>{r.commentaire}</Text> : null}
              </Card>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
}

function Badge({ label, color }) {
  return (
    <View style={[styles.badge, { backgroundColor: color + '15' }]}>
      <Text style={[styles.badgeText, { color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.bg },
  content: { padding: Spacing.md },
  header: { alignItems: 'center', marginBottom: Spacing.lg, paddingTop: Spacing.md },
  avatar: {
    width: 80, height: 80, borderRadius: 40, backgroundColor: Colors.earth,
    alignItems: 'center', justifyContent: 'center',
  },
  username: { fontSize: 20, fontWeight: 'bold', color: Colors.night, marginTop: Spacing.sm },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: Spacing.xs },
  ratingText: { fontSize: 15, fontWeight: '600', color: Colors.night },
  badges: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: Radius.full },
  badgeText: { fontSize: 12, fontWeight: '600' },
  bio: { fontSize: 14, color: Colors.text, lineHeight: 20 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: Colors.night, marginBottom: Spacing.sm, marginTop: Spacing.sm },
  reviewHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  reviewAuthor: { fontSize: 13, fontWeight: '600', color: Colors.earth },
  stars: { flexDirection: 'row' },
  reviewComment: { fontSize: 13, color: Colors.textLight, marginTop: 4 },
});
