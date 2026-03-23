import React from 'react';
import { StatusBar, ActivityIndicator, View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import { Colors } from './src/theme';

// Auth screens
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';

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
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
}

function HomeTabs() {
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
      <Tab.Screen name="DashboardTab" component={DashboardScreen} options={{ title: 'Accueil', headerTitle: 'Covoiturage' }} />
      <Tab.Screen name="SearchTab" component={SearchScreen} options={{ title: 'Rechercher', headerTitle: 'Rechercher un trajet' }} />
      <Tab.Screen name="MatchesTab" component={MatchesScreen} options={{ title: 'Matchs', headerTitle: 'Mes matchs' }} />
      <Tab.Screen name="NotificationsTab" component={NotificationsScreen} options={{ title: 'Notifs', headerTitle: 'Notifications' }} />
      <Tab.Screen name="ProfileTab" component={ProfileScreen} options={{ title: 'Profil', headerTitle: 'Mon profil' }} />
    </Tab.Navigator>
  );
}

function MainStack() {
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="HomeTabs" component={HomeTabs} options={{ headerShown: false }} />
      <Stack.Screen name="AddTrip" component={AddTripScreen} options={{ title: 'Publier un trajet' }} />
      <Stack.Screen name="AddDemande" component={AddDemandeScreen} options={{ title: 'Poster une demande' }} />
      <Stack.Screen name="TripDetail" component={TripDetailScreen} options={{ title: 'Détails du trajet' }} />
      <Stack.Screen name="PublicProfile" component={PublicProfileScreen} options={{ title: 'Profil' }} />
      <Stack.Screen name="Conversation" component={ConversationScreen} options={{ title: 'Conversation' }} />
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
      <AuthProvider>
        <NavigationContainer>
          <StatusBar barStyle="light-content" backgroundColor={Colors.earth} />
          <RootNavigator />
        </NavigationContainer>
      </AuthProvider>
    </ErrorBoundary>
  );
}


