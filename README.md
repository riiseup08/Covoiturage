# Covoit.Africa

Application de covoiturage pour l'Afrique : publiez des trajets, trouvez des passagers ou des conducteurs, validez vos matchs et laissez des avis après le trajet.

## Fonctionnalités

- **Landing** : page d'accueil avec présentation et « Comment ça marche »
- **Inscription / Connexion** : comptes utilisateur avec profil (bio, téléphone, conducteur)
- **Trajets** : publication avec ville départ/arrivée, date, lieu de ramassage, plaque, modèle véhicule, type de bagage accepté
- **Demandes** : publication d'une demande de trajet (passager)
- **Recherche** : filtres par ville, date, bagage, prix max, places min ; pagination
- **Matchs** : correspondances automatiques ; validation ou refus par le conducteur ; annulation par le passager
- **Avis** : notation 1–5 et commentaire après un trajet terminé (affichée sur le profil public)
- **Trajet terminé** : marquer un trajet comme terminé (masqué des recherches)

## Prérequis

- Python 3.10+
- pip

## Installation

```bash
# Cloner le dépôt (ou extraire l'archive)
cd Covoiturage

# Créer un environnement virtuel
python -m venv env

# Activer l'environnement
# Windows (PowerShell) :
.\env\Scripts\Activate.ps1
# Windows (cmd) :
.\env\Scripts\activate.bat
# Linux / macOS :
source env/bin/activate

# Installer les dépendances
pip install django

# Appliquer les migrations
python manage.py migrate

# (Optionnel) Créer un superutilisateur pour l'admin
python manage.py createsuperuser
```

## Lancer l'application

```bash
python manage.py runserver
```

Ouvrir **http://127.0.0.1:8000/** dans le navigateur.

## Variables d'environnement

### Général
- `DJANGO_SECRET_KEY` : clé secrète (obligatoire en production)
- `DJANGO_DEBUG` : `true` ou `false` (défaut : `false`)
- `ALLOWED_HOSTS` : domaines autorisés, séparés par des virgules (ex. `covoiturage-xxx.onrender.com,localhost`)
- `CSRF_TRUSTED_ORIGINS` : origines HTTPS pour les formulaires (ex. `https://covoiturage-xxx.onrender.com`)

### Email (production – mot de passe oublié, etc.)

Sans config email en production, l’app n’envoie pas d’emails (pas de crash). Pour activer l’envoi (SMTP) :

| Variable | Exemple | Description |
|----------|---------|-------------|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Backend SMTP |
| `EMAIL_HOST` | `smtp.gmail.com` ou `smtp.sendgrid.net` | Serveur SMTP |
| `EMAIL_PORT` | `587` | Port (souvent 587 TLS, 465 SSL) |
| `EMAIL_USE_TLS` | `true` | Utiliser TLS |
| `EMAIL_USE_SSL` | `false` | Ou SSL (port 465) |
| `EMAIL_HOST_USER` | Votre adresse ou identifiant SMTP | |
| `EMAIL_HOST_PASSWORD` | Mot de passe ou clé API | |
| `DEFAULT_FROM_EMAIL` | `noreply@votredomaine.com` | Expéditeur des emails |

**Exemple (Render)** : dans le dashboard Render → votre service → Environment, ajouter ces variables. Pour Gmail : activer « Accès moins sécurisé » ou utiliser un mot de passe d’application.

## Structure du projet

- `carpoolconfig/` : configuration Django (settings, urls racine)
- `covoiturage/` : application principale (models, views, forms, signals)
- `templates/` : templates HTML (landing, dashboard, formulaires, 404)

## Licence

Projet à but éducatif / démonstration.
