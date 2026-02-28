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

## Variables d'environnement (optionnel)

- `DJANGO_SECRET_KEY` : clé secrète (production)
- `DJANGO_DEBUG` : `True` ou `False` (défaut : `True`)
- `ALLOWED_HOSTS` : liste séparée par des virgules, ex. `localhost,127.0.0.1,mondomaine.com`

## Structure du projet

- `carpoolconfig/` : configuration Django (settings, urls racine)
- `covoiturage/` : application principale (models, views, forms, signals)
- `templates/` : templates HTML (landing, dashboard, formulaires, 404)

## Licence

Projet à but éducatif / démonstration.
