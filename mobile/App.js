import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Colors } from './src/theme';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { I18nProvider, useI18n } from './src/i18n';
import OfflineBanner from './src/components/OfflineBanner';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import PhoneLoginScreen from './src/screens/PhoneLoginScreen';
import PhoneVerifyScreen from './src/screens/PhoneVerifyScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import SearchScreen from './src/screens/SearchScreen';
import MatchesScreen from './src/screens/MatchesScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import AddTripScreen from './src/screens/AddTripScreen';
import AddDemandeScreen from './src/screens/AddDemandeScreen';
import TripDetailScreen from './src/screens/TripDetailScreen';
import ConversationScreen from './src/screens/ConversationScreen';
import PublicProfileScreen from './src/screens/PublicProfileScreen';
import PaymentScreen from './src/screens/PaymentScreen';
import TransactionConfirmationScreen from './src/screens/TransactionConfirmationScreen';
import WalletScreen from './src/screens/WalletScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function HomeTabs() {
  const { t } = useI18n();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ color, size }) => {
          const icons = {
            Home: 'home',
            Search: 'search',
            Matches: 'git-compare',
            NotificationsTab: 'notifications',
            Profile: 'person',
          };
          return <Ionicons name={icons[route.name] || 'ellipse'} size={size} color={color} />;
        },
        tabBarActiveTintColor: Colors.earth,
        tabBarInactiveTintColor: Colors.textMuted,
        headerShown: false,
      })}
    >
      <Tab.Screen name="Home" component={DashboardScreen} options={{ title: t('tabHome') }} />
      <Tab.Screen name="Search" component={SearchScreen} options={{ title: t('tabSearch') }} />
      <Tab.Screen name="Matches" component={MatchesScreen} options={{ title: t('tabMatches') }} />
      <Tab.Screen name="NotificationsTab" component={NotificationsScreen} options={{ title: t('tabNotifs') }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ title: t('tabProfile') }} />
    </Tab.Navigator>
  );
}

function AppNavigator() {
  const { user, loading } = useAuth();
  const { t } = useI18n();

  if (loading) return null;

  return (
    <Stack.Navigator screenOptions={{ headerStyle: { backgroundColor: Colors.bg }, headerTintColor: Colors.earth }}>
      {!user ? (
        <>
          <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
          <Stack.Screen name="Register" component={RegisterScreen} options={{ title: t('register') }} />
          <Stack.Screen name="PhoneLogin" component={PhoneLoginScreen} options={{ title: t('phoneLogin') }} />
          <Stack.Screen name="PhoneVerify" component={PhoneVerifyScreen} options={{ title: t('verifyCode') }} />
        </>
      ) : (
        <>
          <Stack.Screen name="Main" component={HomeTabs} options={{ headerShown: false }} />
          <Stack.Screen name="AddTrip" component={AddTripScreen} options={{ title: t('publishTrip') }} />
          <Stack.Screen name="AddDemande" component={AddDemandeScreen} options={{ title: t('postRequest') }} />
          <Stack.Screen name="TripDetail" component={TripDetailScreen} options={{ title: t('tripDetails') }} />
          <Stack.Screen name="Conversation" component={ConversationScreen} options={{ title: t('conversation') }} />
          <Stack.Screen name="PublicProfile" component={PublicProfileScreen} options={{ title: '' }} />
          <Stack.Screen name="Payment" component={PaymentScreen} options={{ title: t('payment') }} />
          <Stack.Screen name="TransactionConfirmation" component={TransactionConfirmationScreen} />
          <Stack.Screen name="Wallet" component={WalletScreen} options={{ title: t('wallet') }} />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <I18nProvider>
        <AuthProvider>
          <NavigationContainer>
            <OfflineBanner />
            <AppNavigator />
            <StatusBar style="dark" />
          </NavigationContainer>
        </AuthProvider>
      </I18nProvider>
    </SafeAreaProvider>
  );
}
