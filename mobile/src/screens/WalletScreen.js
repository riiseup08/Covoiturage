import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
  RefreshControl,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';
import { wallet as walletApi } from '../api/client';
import { Colors, Spacing, Radius } from '../theme';

export default function WalletScreen() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [walletData, setWalletData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [topupModal, setTopupModal] = useState(false);
  const [topupAmount, setTopupAmount] = useState('5000');

  useEffect(() => {
    fetchWallet();
  }, []);

  const fetchWallet = async () => {
    try {
      const data = await walletApi.balance();
      setWalletData(data);
    } catch (error) {
      Alert.alert(t('error'), t('failedToLoadWallet'));
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchWallet();
    setRefreshing(false);
  };

  const handleRequestTopup = async () => {
    if (!topupAmount || parseFloat(topupAmount) < 100) {
      Alert.alert(t('error'), t('minimumTopup'));
      return;
    }

    try {
      Alert.alert(
        t('confirmTopup'),
        `${topupAmount} XAF`,
        [
          { text: t('cancel'), onPress: () => {} },
          {
            text: t('confirm'),
            onPress: async () => {
              setTopupModal(false);
              Alert.alert(t('success'), t('topupInitiated'));
              setTimeout(fetchWallet, 3000);
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert(t('error'), error.message);
    }
  };

  if (loading || !walletData) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.earth} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.earth} />}
    >
      <View style={[styles.balanceCard, walletData.low_balance && styles.lowBalanceCard]}>
        <Text style={styles.balanceLabel}>{t('walletBalance')}</Text>
        <View style={styles.balanceRow}>
          <Text style={styles.balanceAmount}>{walletData.balance}</Text>
          <Text style={styles.currencyText}>{walletData.currency}</Text>
        </View>

        {walletData.low_balance && (
          <View style={styles.lowBalanceWarning}>
            <MaterialCommunityIcons name="alert-circle" size={16} color={Colors.warning} />
            <Text style={styles.lowBalanceText}>{t('lowBalance')}</Text>
          </View>
        )}

        <Text style={styles.walletInfo}>{t('walletDescription')}</Text>
      </View>

      <TouchableOpacity
        style={styles.topupButton}
        onPress={() => setTopupModal(!topupModal)}
      >
        <MaterialCommunityIcons name="plus-circle" size={20} color={Colors.white} />
        <Text style={styles.topupButtonText}>{t('addBalance')}</Text>
      </TouchableOpacity>

      {topupModal && (
        <View style={styles.topupForm}>
          <Text style={styles.formTitle}>{t('topupAmount')}</Text>

          <View style={styles.quickAmounts}>
            {['5000', '10000', '25000'].map((amount) => (
              <TouchableOpacity
                key={amount}
                style={[
                  styles.quickAmountBtn,
                  topupAmount === amount && styles.quickAmountBtnActive,
                ]}
                onPress={() => setTopupAmount(amount)}
              >
                <Text
                  style={[
                    styles.quickAmountText,
                    topupAmount === amount && styles.quickAmountTextActive,
                  ]}
                >
                  {amount}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={styles.confirmButton} onPress={handleRequestTopup}>
            <Text style={styles.confirmButtonText}>
              {t('topUp')} {topupAmount} XAF
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.cancelBtn} onPress={() => setTopupModal(false)}>
            <Text style={styles.cancelBtnText}>{t('cancel')}</Text>
          </TouchableOpacity>
        </View>
      )}

      {walletData.recent_transactions && walletData.recent_transactions.length > 0 && (
        <View style={styles.transactionsContainer}>
          <Text style={styles.sectionTitle}>{t('recentTransactions')}</Text>

          {walletData.recent_transactions.map((transaction) => (
            <View key={transaction.id} style={styles.transactionItem}>
              <View style={styles.transactionLeft}>
                <MaterialCommunityIcons
                  name={
                    transaction.transaction_type === 'topup'
                      ? 'plus-circle'
                      : transaction.transaction_type === 'commission_deducted'
                      ? 'minus-circle'
                      : 'sync'
                  }
                  size={24}
                  color={
                    transaction.transaction_type === 'topup'
                      ? Colors.success
                      : transaction.transaction_type === 'commission_deducted'
                      ? Colors.danger
                      : Colors.earth
                  }
                />
                <View style={styles.transactionDetails}>
                  <Text style={styles.transactionType}>{transaction.type_display}</Text>
                  <Text style={styles.transactionDate}>
                    {new Date(transaction.created_at).toLocaleDateString('fr-FR')}
                  </Text>
                </View>
              </View>

              <Text
                style={[
                  styles.transactionAmount,
                  transaction.transaction_type === 'topup' && styles.transactionAmountPositive,
                  transaction.transaction_type === 'commission_deducted' && styles.transactionAmountNegative,
                ]}
              >
                {transaction.transaction_type === 'topup' ? '+' : '-'}
                {transaction.amount}
              </Text>
            </View>
          ))}
        </View>
      )}

      {walletData.recent_transactions && walletData.recent_transactions.length === 0 && (
        <View style={styles.emptyState}>
          <MaterialCommunityIcons name="wallet-outline" size={48} color={Colors.border} />
          <Text style={styles.emptyStateText}>{t('noTransactions')}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg,
    paddingTop: Spacing.md,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.bg,
  },
  balanceCard: {
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.md,
    backgroundColor: Colors.earth,
    borderRadius: Radius.lg,
    padding: Spacing.lg,
  },
  lowBalanceCard: {
    backgroundColor: Colors.warning,
  },
  balanceLabel: {
    color: Colors.white,
    fontSize: 14,
    fontWeight: '500',
    opacity: 0.9,
  },
  balanceRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginTop: Spacing.sm,
    marginBottom: Spacing.md,
  },
  balanceAmount: {
    color: Colors.white,
    fontSize: 32,
    fontWeight: 'bold',
  },
  currencyText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: '600',
    marginLeft: Spacing.sm,
  },
  lowBalanceWarning: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: Radius.sm,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    alignItems: 'center',
  },
  lowBalanceText: {
    color: Colors.white,
    fontSize: 13,
    fontWeight: '500',
    marginLeft: Spacing.sm,
  },
  walletInfo: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 13,
    fontStyle: 'italic',
  },
  topupButton: {
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.md,
    backgroundColor: Colors.success,
    flexDirection: 'row',
    borderRadius: Radius.md,
    padding: Spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  topupButtonText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: '600',
    marginLeft: Spacing.sm,
  },
  topupForm: {
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.md,
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  formTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.night,
    marginBottom: Spacing.md,
  },
  quickAmounts: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.md,
  },
  quickAmountBtn: {
    flex: 1,
    marginHorizontal: Spacing.xs,
    paddingVertical: Spacing.sm + 2,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.sm,
    alignItems: 'center',
  },
  quickAmountBtnActive: {
    backgroundColor: Colors.earth,
    borderColor: Colors.earth,
  },
  quickAmountText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.night,
  },
  quickAmountTextActive: {
    color: Colors.white,
  },
  confirmButton: {
    backgroundColor: Colors.success,
    borderRadius: Radius.md,
    padding: Spacing.md,
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  confirmButtonText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  cancelBtn: {
    backgroundColor: Colors.borderLight,
    borderRadius: Radius.md,
    padding: Spacing.md - 2,
    alignItems: 'center',
  },
  cancelBtnText: {
    color: Colors.night,
    fontSize: 14,
    fontWeight: '500',
  },
  transactionsContainer: {
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.night,
    marginBottom: Spacing.md,
  },
  transactionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  transactionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  transactionDetails: {
    marginLeft: Spacing.md,
    flex: 1,
  },
  transactionType: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.night,
  },
  transactionDate: {
    fontSize: 12,
    color: Colors.textMuted,
    marginTop: 2,
  },
  transactionAmount: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.night,
  },
  transactionAmountPositive: {
    color: Colors.success,
  },
  transactionAmountNegative: {
    color: Colors.danger,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    marginTop: Spacing.md,
    fontSize: 14,
    color: Colors.textMuted,
  },
});
