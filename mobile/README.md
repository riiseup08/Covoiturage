# Covoit.Africa — Mobile Carpooling App

A React Native (Expo) carpooling application for Africa, with a Django REST backend.

## Tech Stack

| Layer     | Technology |
|-----------|-----------|
| Mobile    | React Native / Expo |
| Web       | React Native Web |
| Backend   | Django REST Framework |
| Auth      | Token auth + Phone OTP (Africa's Talking / Twilio) |
| Payments  | Mobile Money (MTN, Orange, Moov, Airtel, Wave) |
| Storage   | AsyncStorage (offline cache, 30-min TTL) |
| i18n      | French (default) + English |

## Project Structure

```
mobile/
├── src/
│   ├── api/client.js          # API client (fetch wrapper, token mgmt)
│   ├── components/            # Reusable UI components
│   │   ├── Button.js          # Primary/secondary/danger button
│   │   ├── Card.js            # Elevated card container
│   │   ├── DatePicker.js      # Cross-platform date picker
│   │   ├── Input.js           # Text input with label & error
│   │   ├── OfflineBanner.js   # Network status banner
│   │   └── TripCard.js        # Trip summary card
│   ├── context/AuthContext.js  # Auth state (user, token, login/logout)
│   ├── i18n/                  # Translations (en.js, fr.js)
│   ├── screens/               # App screens
│   │   ├── DashboardScreen.js
│   │   ├── SearchScreen.js
│   │   ├── MatchesScreen.js
│   │   ├── NotificationsScreen.js
│   │   ├── ProfileScreen.js
│   │   ├── AddTripScreen.js
│   │   ├── AddDemandeScreen.js
│   │   ├── ConversationScreen.js
│   │   ├── WalletScreen.js
│   │   ├── PaymentScreen.js
│   │   └── ...
│   ├── theme/index.js          # Earth-tone design tokens (Colors, Spacing, Radius)
│   └── utils/offline.js        # Cache utilities (getCached, setCache, fetchWithCache)
├── web/index.html              # Web entry point
└── scripts/                    # Image optimization scripts
templates/                      # Django HTML templates
scripts/                        # Backend utility scripts
```

## Getting Started

### Prerequisites

- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- A running Django backend at `http://localhost:8000`

### Install Dependencies

```bash
cd mobile
npm install
```

### Run the App

```bash
# iOS
npx expo start --ios

# Android
npx expo start --android

# Web
npx expo start --web
```

### Backend API

The mobile app connects to:
- **Web**: `http://localhost:8000/api`
- **Native**: `http://<YOUR_IP>:8000/api` (edit `src/api/client.js`)

## API Endpoints

| Group         | Endpoint                  | Method |
|---------------|---------------------------|--------|
| Auth          | `/api/auth/login/`        | POST   |
| Auth          | `/api/auth/register/`     | POST   |
| Auth          | `/api/auth/logout/`       | POST   |
| Phone OTP     | `/api/auth/phone/request-otp/` | POST |
| Phone OTP     | `/api/auth/phone/verify-otp/`  | POST |
| Profile       | `/api/profile/`           | GET    |
| Profile       | `/api/profile/update/`    | PATCH  |
| Voyages       | `/api/voyages/search/`    | GET    |
| Voyages       | `/api/voyages/create/`    | POST   |
| Matches       | `/api/matches/`           | GET    |
| Notifications | `/api/notifications/`     | GET    |
| Wallet        | `/api/wallet/balance/`    | GET    |
| Payments      | `/api/payments/create/`   | POST   |

## Design System

Earth-tone palette defined in `src/theme/index.js`:

| Token       | Value     | Usage                  |
|-------------|-----------|------------------------|
| `Colors.earth`     | `#6B4226` | Primary brand color    |
| `Colors.sun`       | `#E8A317` | Accent / warnings      |
| `Colors.night`     | `#2C1810` | Headings               |
| `Colors.bg`        | `#FAF6F1` | Page background        |
| `Colors.bgCard`    | `#FFFFFF` | Card background        |
| `Colors.success`   | `#27AE60` | Success states         |
| `Colors.danger`    | `#E74C3C` | Errors / destructive   |

## Internationalization

Two languages supported: French (`fr.js`, default) and English (`en.js`).

Usage in screens:
```js
import { useI18n } from '../i18n';

const { t, lang, setLang } = useI18n();
// t('greeting') → "Bonjour 👋" or "Hello 👋"
```

## Offline Support

Data is cached in AsyncStorage with a 30-minute TTL. When the API is unreachable, cached data is served as fallback.

```js
import { fetchWithCache } from '../utils/offline';

const { data, fromCache } = await fetchWithCache('cache_key', () => api.call());
```

## Testing

```bash
cd mobile
npx jest
```

Tests are in `src/__tests__/`:
- `offline.test.js` — Cache utilities
- `client.test.js` — API client & token management
- `i18n.test.js` — Translation completeness
- `components.test.js` — UI component rendering

## Currency & Region

- Default currency: **XAF** (Central African CFA franc)
- Default country code: **+237** (Cameroon)
- Mobile Money providers: MTN, Orange, Moov, Airtel, Wave
