import React from 'react';
import { StatusBar, ActivityIndicator, View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import { I18nProvider, useI18n } from './src/i18n';
import { Colors } from './src/theme';
import OfflineBanner from './src/components/OfflineBanner';

// Auth screens
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import PhoneLoginScreen from './src/screens/PhoneLoginScreen';
import PhoneVerifyScreen from './src/screens/PhoneVerifyScreen';

// Main screens
import DashboardScreen from './src/screens/DashboardScreen';
import SearchScreen from './src/screens/SearchScreen';
import AddTripScreen from './src/screens/AddTripScreen';
import AddDemandeScreen from './src/screens/AddDemandeScreen';
import TripDetailScreen from './src/screens/TripDetailScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import PublicProfileScreen from './src/screens/PublicProfileScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';
import MatchesScreen from './src/screens/MatchesScreen';
import ConversationScreen from './src/screens/ConversationScreen';
import PaymentScreen from './src/screens/PaymentScreen';
import WalletScreen from './src/screens/WalletScreen';
import TransactionConfirmationScreen from './src/screens/TransactionConfirmationScreen';

// Error boundary to catch and display runtime errors on web
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20, backgroundColor: '#faf6f1' }}>
          <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#c00', marginBottom: 10 }}>App Error</Text>
          <Text style={{ fontSize: 14, color: '#333', textAlign: 'center' }}>{String(this.state.error)}</Text>
        </View>
      );
    }
    return this.props.children;
  }
}

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const screenOptions = {
  headerStyle: { backgroundColor: Colors.earth },
  headerTintColor: Colors.white,
  headerTitleStyle: { fontWeight: '600' },
};

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="PhoneLogin" component={PhoneLoginScreen} />
      <Stack.Screen name="PhoneVerify" component={PhoneVerifyScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
}

function HomeTabs() {
  const { t } = useI18n();
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        ...screenOptions,
        tabBarActiveTintColor: Colors.earth,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarStyle: { backgroundColor: Colors.bgCard, borderTopColor: Colors.borderLight, paddingBottom: 4, height: 56 },
        tabBarIcon: ({ focused, color, size }) => {
          const icons = {
            DashboardTab: focused ? 'home' : 'home-outline',
            SearchTab: focused ? 'search' : 'search-outline',
            MatchesTab: focused ? 'git-compare' : 'git-compare-outline',
            NotificationsTab: focused ? 'notifications' : 'notifications-outline',
            ProfileTab: focused ? 'person' : 'person-outline',
          };
          return <Ionicons name={icons[route.name]} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="DashboardTab" component={DashboardScreen} options={{ title: t('tabHome'), headerTitle: 'Covoiturage' }} />
      <Tab.Screen name="SearchTab" component={SearchScreen} options={{ title: t('tabSearch'), headerTitle: t('searchTitle') }} />
      <Tab.Screen name="MatchesTab" component={MatchesScreen} options={{ title: t('tabMatches'), headerTitle: t('myMatches') }} />
      <Tab.Screen name="NotificationsTab" component={NotificationsScreen} options={{ title: t('tabNotifs'), headerTitle: t('notifications') }} />
      <Tab.Screen name="ProfileTab" component={ProfileScreen} options={{ title: t('tabProfile'), headerTitle: t('myProfile') }} />
    </Tab.Navigator>
  );
}

function MainStack() {
  const { t } = useI18n();
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="HomeTabs" component={HomeTabs} options={{ headerShown: false }} />
      <Stack.Screen name="AddTrip" component={AddTripScreen} options={{ title: t('publishTrip') }} />
      <Stack.Screen name="AddDemande" component={AddDemandeScreen} options={{ title: t('postRequest') }} />
      <Stack.Screen name="TripDetail" component={TripDetailScreen} options={{ title: t('tripDetails') }} />
      <Stack.Screen name="PublicProfile" component={PublicProfileScreen} options={{ title: t('tabProfile') }} />
      <Stack.Screen name="Conversation" component={ConversationScreen} options={{ title: 'Conversation' }} />
      <Stack.Screen name="Payment" component={PaymentScreen} options={{ title: t('paymentTitle') }} />
      <Stack.Screen name="TransactionConfirmation" component={TransactionConfirmationScreen} options={{ title: t('confirmPayment') }} />
      <Stack.Screen name="Wallet" component={WalletScreen} options={{ title: t('wallet') }} />
    </Stack.Navigator>
  );
}

function RootNavigator() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.bg }}>
        <ActivityIndicator size="large" color={Colors.earth} />
      </View>
    );
  }

  return user ? <MainStack /> : <AuthStack />;
}

export default function App() {
  return (
    <ErrorBoundary>
      <I18nProvider>
        <AuthProvider>
          <NavigationContainer>
            <StatusBar barStyle="light-content" backgroundColor={Colors.earth} />
            <OfflineBanner />
            <RootNavigator />
          </NavigationContainer>
        </AuthProvider>
      </I18nProvider>
    </ErrorBoundary>
  );
}


