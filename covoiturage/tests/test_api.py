import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from covoiturage.models import Voyage, Demande, Correspondance, Profile
from datetime import timedelta
from django.utils import timezone


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def driver_api_client(api_client, driver):
    """Return an authenticated API client for driver."""
    api_client.force_authenticate(user=driver)
    return api_client


@pytest.mark.django_db
class TestVoyageAPI:
    """Tests for Voyage API endpoints."""

    def test_list_voyages_unauthenticated(self, api_client, voyage):
        """List voyages should be accessible without auth."""
        response = api_client.get("/api/voyages/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_voyages_only_active(self, api_client, completed_voyage):
        """Completed voyages should not appear in list."""
        response = api_client.get("/api/voyages/")
        assert response.status_code == status.HTTP_200_OK
        voyage_ids = [v["id"] for v in response.data["results"]]
        assert completed_voyage.id not in voyage_ids

    def test_create_voyage_authenticated(self, authenticated_api_client):
        """Creating voyage should work for authenticated users."""
        data = {
            "ville_depart": "Douala",
            "ville_arrivee": "Yaoundé",
            "date_depart": (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "date_arrivee": (timezone.now() + timedelta(days=1, hours=4)).strftime("%Y-%m-%d %H:%M"),
            "places_disponibles": 2,
            "prix_par_place": 5000.00,
            "plaque_immatriculation": "CE 1234 AB",
            "modele_voiture": "Toyota Corolla",
            "type_bagage_accepte": "moyen",
        }
        response = authenticated_api_client.post("/api/voyages/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Voyage.objects.filter(ville_depart="Douala").exists()

    def test_create_voyage_unauthenticated(self, api_client):
        """Creating voyage should require auth."""
        data = {
            "ville_depart": "Douala",
            "ville_arrivee": "Yaoundé",
        }
        response = api_client.post("/api/voyages/", data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_voyage(self, api_client, voyage):
        """Retrieving voyage should work."""
        response = api_client.get(f"/api/voyages/{voyage.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["ville_depart"] == "Douala"

    def test_search_voyages(self, authenticated_api_client, voyage):
        """Search should filter voyages correctly."""
        response = authenticated_api_client.get(
            "/api/voyages/search/", {"ville_depart": "Douala"}
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDemandeAPI:
    """Tests for Demande API endpoints."""

    def test_list_demandes_authenticated(self, authenticated_api_client, demande):
        """List demandes should be accessible for owner."""
        response = authenticated_api_client.get("/api/demandes/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_demande(self, authenticated_api_client):
        """Creating demande should work."""
        data = {
            "ville_depart": "Kribi",
            "ville_arrivee": "Douala",
            "date_voyage": (timezone.now().date() + timedelta(days=2)).isoformat(),
            "places": 1,
        }
        response = authenticated_api_client.post("/api/demandes/", data)
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestCorrespondanceAPI:
    """Tests for Correspondance API endpoints."""

    def test_list_correspondances(self, authenticated_api_client, correspondance):
        """List correspondances should work."""
        response = authenticated_api_client.get("/api/correspondances/")
        assert response.status_code == status.HTTP_200_OK

    def test_validate_correspondance_driver(self, driver_api_client, correspondance):
        """Driver should be able to validate."""
        response = driver_api_client.post(
            f"/api/correspondances/{correspondance.id}/validate/"
        )
        assert response.status_code == status.HTTP_200_OK
        correspondance.refresh_from_db()
        assert correspondance.is_validated == True


@pytest.mark.django_db
class TestProfileAPI:
    """Tests for Profile API endpoints."""

    def test_get_public_profile(self, api_client, user):
        """Getting public profile should work."""
        response = api_client.get(f"/api/profiles/{user.profile.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_get_my_profile(self, authenticated_api_client, user):
        """Getting own profile should work."""
        response = authenticated_api_client.get("/api/profiles/me/")
        assert response.status_code == status.HTTP_200_OK

    def test_update_my_profile(self, authenticated_api_client, user):
        """Updating own profile should work."""
        data = {"bio": "Test bio"}
        response = authenticated_api_client.patch("/api/profiles/me/", data)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestNotificationAPI:
    """Tests for Notification API endpoints."""

    def test_list_notifications(self, authenticated_api_client, user):
        """List notifications should work."""
        response = authenticated_api_client.get("/api/notifications/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, api_client):
        """Health check should return healthy status."""
        response = api_client.get("/api/health/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
