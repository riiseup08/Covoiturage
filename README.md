# Covoiturage.Africa

Carpooling application for Africa: post trips, find passengers or drivers, validate your matches, and leave reviews after the trip.

## Features

- **Landing Page**: Home page with presentation and "How it works"
- **Registration / Login**: User accounts with profile (bio, phone, driver status)
- **Trips**: Post trips with departure/arrival cities, date, pickup location, license plate, vehicle model, accepted luggage type
- **Requests**: Post a trip request (passenger)
- **Search**: Filters by city, date, luggage, max price, min seats; pagination
- **Matches**: Automatic matching; validation or refusal by driver; cancellation by passenger
- **Reviews**: 1-5 star rating and comment after a completed trip (displayed on public profile)
- **Trip Completed**: Mark a trip as completed (hidden from searches)
- **REST API**: JSON endpoints for mobile integration
- **Tests**: Complete unit test suite

## Prerequisites

- Python 3.10+
- pip
- Redis (optional, for caching)

## Installation

```bash
# Clone the repository (or extract the archive)
cd Covoiturage

# Create a virtual environment
python -m venv env

# Activate the environment
# Windows (PowerShell):
.\env\Scripts\Activate.ps1
# Windows (cmd):
.\env\Scripts\activate.bat
# Linux / macOS:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Redis for caching
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux/macOS: redis-server

# Apply migrations
python manage.py migrate

# (Optional) Create a superuser for admin
python manage.py createsuperuser
```

## Launch the Application

```bash
# Development mode
python manage.py runserver

# Production mode (with Gunicorn)
gunicorn carpoolconfig.wsgi:application
```

Open **http://127.0.0.1:8000/** in your browser.

## Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=covoiturage --cov-report=html

# Specific tests
pytest covoiturage/tests/test_models.py -v
pytest covoiturage/tests/test_views.py -v
pytest covoiturage/tests/test_api.py -v
```

## API REST

L'API est disponible sur `/api/`. Endpoints principaux:

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | /api/voyages/ | Liste des trajets |
| POST | /api/voyages/ | Créer un trajet |
| GET | /api/voyages/{id}/ | Détail d'un trajet |
| GET | /api/demandes/ | Liste des demandes |
| POST | /api/demandes/ | Créer une demande |
| GET | /api/search/ | Recherche avec filtres |
| GET | /api/profile/{username}/ | Profil public |

Authentification: Token JWT (obtenu via `/api/auth/token/`)

## Variables d'environnement

### Général
- `DJANGO_SECRET_KEY` : clé secrète (obligatoire en production)
- `DJANGO_DEBUG` : `true` ou `false` (défaut : `false`)
- `DJANGO_ENV` : `development` ou `production` (défaut : `development`)
- `ALLOWED_HOSTS` : domaines autorisés, séparés par des virgules
- `CSRF_TRUSTED_ORIGINS` : origines HTTPS pour les formulaires

### Redis (Caching)
- `REDIS_URL` : URL Redis (défaut : `redis://localhost:6379/0`)

### Email (production)
| Variable | Description |
|----------|-------------|
| `EMAIL_BACKEND` | Backend SMTP |
| `EMAIL_HOST` | Serveur SMTP |
| `EMAIL_PORT` | Port (souvent 587 TLS) |
| `EMAIL_USE_TLS` | Utiliser TLS |
| `EMAIL_HOST_USER` | Identifiant SMTP |
| `EMAIL_HOST_PASSWORD` | Mot de passe SMTP |
| `DEFAULT_FROM_EMAIL` | Expéditeur |

## Structure du projet

```
Covoiturage/
├── carpoolconfig/        # Configuration Django
│   ├── settings/          # Paramètres (dev/prod)
│   ├── urls.py
│   └── wsgi.py
├── covoiturage/           # Application principale
│   ├── models.py          # Modèles de données
│   ├── views.py           # Vues
│   ├── forms.py           # Formulaires
│   ├── api/               # API REST
│   ├── tests/             # Tests unitaires
│   └── ...
├── templates/             # Templates HTML
├── mobile/                # Application React Native
├── scripts/               # Scripts utilitaires
├── pytest.ini             # Configuration pytest
└── requirements.txt
```

## Licence

Projet à but éducatif / démonstration.
