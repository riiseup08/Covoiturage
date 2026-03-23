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
  SectionList,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n';
import client from '../api/client';

export default function WalletScreen() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [topupModal, setTopupModal] = useState(false);
  const [topupAmount, setTopupAmount] = useState('5000');

  useEffect(() => {
    fetchWallet();
  }, []);

  const fetchWallet = async () => {
    try {
      const data = await client.wallet.balance();
      setWallet(data);
    } catch (error) {
      console.error('Erreur chargement wallet:', error);
      Alert.alert(t('error'), t('failedToLoadWallet', 'Impossible de charger le portefeuille'));
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
      Alert.alert(t('error'), t('minimumTopup', 'Montant minimum: 100 XAF'));
      return;
    }

    try {
      // For now, show a confirmation dialog
      Alert.alert(
        t('confirmTopup', 'Confirmer la recharge'),
        `${topupAmount} XAF seront déduits de votre compte mobile money`,
        [
          { text: t('cancel'), onPress: () => {} },
          {
            text: t('confirm'),
            onPress: async () => {
              setTopupModal(false);
              // Integration with mobile money provider would happen here
              Alert.alert(
                t('success'),
                t('topupInitiated', 'Recharge initiée. Veuillez confirmer sur votre téléphone.')
              );
              setTimeout(fetchWallet, 3000);
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert(t('error'), error.message);
    }
  };

  if (loading || !wallet) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  const sections = [
    {
      title: t('recentTransactions', 'Transactions récentes'),
      data: wallet.recent_transactions || [],
    },
  ];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Balance Card */}
      <View style={[styles.balanceCard, wallet.low_balance && styles.lowBalanceCard]}>
        <Text style={styles.balanceLabel}>{t('walletBalance', 'Solde du portefeuille')}</Text>
        <View style={styles.balanceRow}>
          <Text style={styles.balanceAmount}>{wallet.balance}</Text>
          <Text style={styles.currency}>{wallet.currency}</Text>
        </View>

        {wallet.low_balance && (
          <View style={styles.lowBalanceWarning}>
            <MaterialCommunityIcons name="alert-circle" size={16} color="#FF9500" />
            <Text style={styles.lowBalanceText}>
              {t('lowBalance', 'Solde faible. Faites une recharge.')}
            </Text>
          </View>
        )}

        <Text style={styles.walletInfo}>
          {t('walletDescription', 'Votre portefeuille accumule les commissions sur les trajets en espèces')}
        </Text>
      </View>

      {/* Top-up Button */}
      <TouchableOpacity
        style={styles.topupButton}
        onPress={() => setTopupModal(!topupModal)}
      >
        <MaterialCommunityIcons name="plus-circle" size={20} color="#FFF" />
        <Text style={styles.topupButtonText}>{t('addBalance', 'Ajouter du solde')}</Text>
      </TouchableOpacity>

      {/* Top-up Form */}
      {topupModal && (
        <View style={styles.topupForm}>
          <Text style={styles.formTitle}>{t('topupAmount', 'Montant de la recharge')}</Text>

          {/* Quick amounts */}
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

          {/* Confirm Button */}
          <TouchableOpacity
            style={styles.confirmButton}
            onPress={handleRequestTopup}
          >
            <Text style={styles.confirmButtonText}>
              {t('topup', 'Recharger')} {topupAmount} XAF
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.cancelButton}
            onPress={() => setTopupModal(false)}
          >
            <Text style={styles.cancelButtonText}>{t('cancel')}</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Transaction History */}
      {wallet.recent_transactions && wallet.recent_transactions.length > 0 && (
        <View style={styles.transactionsContainer}>
          <Text style={styles.sectionTitle}>{t('recentTransactions', 'Transactions récentes')}</Text>

          {wallet.recent_transactions.map((transaction) => (
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
                      ? '#34C759'
                      : transaction.transaction_type === 'commission_deducted'
                      ? '#FF3B30'
                      : '#007AFF'
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
                  transaction.transaction_type === 'commission_deducted' &&
                    styles.transactionAmountNegative,
                ]}
              >
                {transaction.transaction_type === 'topup' ? '+' : '-'}
                {transaction.amount}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Driver Info */}
      {wallet.recent_transactions && wallet.recent_transactions.length === 0 && (
        <View style={styles.emptyState}>
          <MaterialCommunityIcons name="wallet-outline" size={48} color="#D0D0D0" />
          <Text style={styles.emptyStateText}>
            {t('noTransactions', 'Aucune transaction pour l\'instant')}
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    paddingTop: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  balanceCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 20,
  },
  lowBalanceCard: {
    backgroundColor: '#FF9500',
  },
  balanceLabel: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '500',
    opacity: 0.9,
  },
  balanceRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginTop: 8,
    marginBottom: 12,
  },
  balanceAmount: {
    color: '#FFF',
    fontSize: 32,
    fontWeight: 'bold',
  },
  currency: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  lowBalanceWarning: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    alignItems: 'center',
  },
  lowBalanceText: {
    color: '#FFF',
    fontSize: 13,
    fontWeight: '500',
    marginLeft: 8,
  },
  walletInfo: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 13,
    fontStyle: 'italic',
  },
  topupButton: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#34C759',
    flexDirection: 'row',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  topupButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  topupForm: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  formTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222',
    marginBottom: 12,
  },
  quickAmounts: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  quickAmountBtn: {
    flex: 1,
    marginHorizontal: 4,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#D0D0D0',
    borderRadius: 8,
    alignItems: 'center',
  },
  quickAmountBtnActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  quickAmountText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#222',
  },
  quickAmountTextActive: {
    color: '#FFF',
  },
  confirmButton: {
    backgroundColor: '#34C759',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginBottom: 8,
  },
  confirmButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelButton: {
    backgroundColor: '#F0F0F0',
    borderRadius: 10,
    padding: 12,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#222',
    fontSize: 14,
    fontWeight: '500',
  },
  transactionsContainer: {
    marginHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#222',
    marginBottom: 12,
  },
  transactionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  transactionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  transactionDetails: {
    marginLeft: 12,
    flex: 1,
  },
  transactionType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222',
  },
  transactionDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  transactionAmount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222',
  },
  transactionAmountPositive: {
    color: '#34C759',
  },
  transactionAmountNegative: {
    color: '#FF3B30',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    marginTop: 12,
    fontSize: 14,
    color: '#999',
  },
});
