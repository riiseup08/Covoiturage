import pytest
from django.contrib.auth.models import User
from covoiturage.models import (
    Profile,
    Voyage,
    Demande,
    Correspondance,
    Avis,
    Notification,
    Wallet,
)
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return a REST Framework API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    user = User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )
    return user


@pytest.fixture
def user2(db):
    """Create a second test user."""
    return User.objects.create_user(
        username="testuser2", email="test2@example.com", password="testpass123"
    )


@pytest.fixture
def driver(db):
    """Create a driver user."""
    user = User.objects.create_user(
        username="driver", email="driver@example.com", password="driverpass123"
    )
    profile = user.profile
    profile.is_driver = True
    profile.save()
    return user


@pytest.fixture
def profile(db, user):
    """Get or create profile for user."""
    return Profile.objects.get_or_create(user=user)[0]


@pytest.fixture
def wallet(db, user):
    """Get or create wallet for user."""
    return Wallet.objects.get_or_create(user=user)[0]


@pytest.fixture
def voyage(db, driver):
    """Create a test voyage (trip)."""
    return Voyage.objects.create(
        conducteur=driver,
        ville_depart="Douala",
        ville_arrivee="Yaoundé",
        date_depart=timezone.now() + timedelta(days=1),
        date_arrivee=timezone.now() + timedelta(days=1, hours=4),
        places_disponibles=3,
        prix_par_place=5000.00,
        plaque_immatriculation="CE 1234 AB",
        modele_voiture="Toyota Corolla",
        type_bagage_accepte="moyen",
    )


@pytest.fixture
def demande(db, user):
    """Create a test demande (request)."""
    return Demande.objects.create(
        passager=user,
        ville_depart="Douala",
        ville_arrivee="Yaoundé",
        date_voyage=timezone.now().date() + timedelta(days=1),
        places=1,
    )


@pytest.fixture
def correspondance(db, voyage, demande):
    """Create a test correspondance (match)."""
    return Correspondance.objects.create(
        voyage=voyage,
        demande=demande,
        score_match=0.85,
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return an authenticated test client."""
    client.force_login(user)
    return client


@pytest.fixture
def authenticated_api_client(api_client, user):
    """Return an authenticated REST API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def driver_api_client(api_client, driver):
    """Return an authenticated API client for driver."""
    api_client.force_authenticate(user=driver)
    return api_client


@pytest.fixture
def completed_voyage(db, driver, user, user2):
    """Create a completed voyage with validated matches."""
    voyage = Voyage.objects.create(
        conducteur=driver,
        ville_depart="Douala",
        ville_arrivee="Bafoussam",
        date_depart=timezone.now() - timedelta(days=1),
        date_arrivee=timezone.now() - timedelta(days=1, hours=3),
        places_disponibles=3,
        prix_par_place=3500.00,
        plaque_immatriculation="CE 5678 CD",
        modele_voiture="Honda Civic",
        type_bagage_accepte="tous",
        est_termine=True,
    )

    demande1 = Demande.objects.create(
        passager=user,
        ville_depart="Douala",
        ville_arrivee="Bafoussam",
        date_voyage=timezone.now().date() - timedelta(days=1),
        places=1,
    )

    Correspondance.objects.create(
        voyage=voyage,
        demande=demande1,
        score_match=0.90,
        is_validated=True,
    )

    return voyage
