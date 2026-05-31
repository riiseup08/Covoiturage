import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from covoiturage.models import Voyage, Demande, Correspondance, Notification
from datetime import timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestLandingView:
    """Tests for landing page."""

    def test_landing_page_loads(self, client):
        """Landing page should load successfully."""
        response = client.get(reverse("covoiturage:landing"))
        assert response.status_code == 200

    def test_landing_uses_correct_template(self, client):
        """Landing page should use correct template."""
        response = client.get(reverse("covoiturage:landing"))
        assert "voyages/landing.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestAuthentication:
    """Tests for authentication views."""

    def test_register_page_loads(self, client):
        """Registration page should load."""
        response = client.get(reverse("covoiturage:register"))
        assert response.status_code == 200

    def test_register_creates_user(self, client):
        """Registration should create new user."""
        response = client.post(
            reverse("covoiturage:register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(username="newuser").exists()

    def test_register_creates_profile(self, client):
        """Registration should create user profile."""
        client.post(
            reverse("covoiturage:register"),
            {
                "username": "newuser2",
                "email": "new2@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        user = User.objects.get(username="newuser2")
        assert hasattr(user, "profile")

    def test_register_creates_wallet(self, client):
        """Registration should create user wallet."""
        client.post(
            reverse("covoiturage:register"),
            {
                "username": "walletuser",
                "email": "wallet@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        user = User.objects.get(username="walletuser")
        assert hasattr(user, "wallet")

    def test_duplicate_email_rejected(self, client, user):
        """Registration should reject duplicate email."""
        response = client.post(
            reverse("covoiturage:register"),
            {
                "username": "anotheruser",
                "email": user.email,
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        assert response.status_code == 200
        assert "Un compte existe déjà" in response.content.decode()


@pytest.mark.django_db
class TestDashboard:
    """Tests for dashboard views."""

    def test_dashboard_requires_login(self, client):
        """Dashboard should require authentication."""
        response = client.get(reverse("covoiturage:dashboard"))
        assert response.status_code == 302

    def test_dashboard_loads_for_authenticated(self, authenticated_client):
        """Dashboard should load for authenticated users."""
        response = authenticated_client.get(reverse("covoiturage:dashboard"))
        assert response.status_code == 200

    def test_dashboard_shows_user_stats(self, authenticated_client, voyage, demande):
        """Dashboard should show user statistics."""
        response = authenticated_client.get(reverse("covoiturage:dashboard"))
        assert response.status_code == 200
        context = response.context
        assert "stats" in context


@pytest.mark.django_db
class TestVoyageViews:
    """Tests for voyage CRUD operations."""

    def test_add_voyage_page_loads(self, authenticated_client):
        """Add voyage page should load."""
        response = authenticated_client.get(reverse("covoiturage:add_voyage"))
        assert response.status_code == 200

    def test_add_voyage_creates_voyage(self, authenticated_client, driver):
        """Adding voyage should create new voyage."""
        data = {
            "ville_depart": "Bertoua",
            "ville_arrivee": "Ebolowa",
            "date_depart": (timezone.now() + timedelta(days=2)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "date_arrivee": (timezone.now() + timedelta(days=2, hours=3)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "places_disponibles": 2,
            "prix_par_place": 4000.00,
            "plaque_immatriculation": "CE 9999 ZZ",
            "modele_voiture": "Renault Clio",
            "type_bagage_accepte": "moyen",
        }
        response = authenticated_client.post(reverse("covoiturage:add_voyage"), data)
        assert response.status_code == 302
        assert Voyage.objects.filter(ville_depart="Bertoua").exists()

    def test_edit_voyage_loads(self, authenticated_client, voyage, driver):
        """Edit voyage page should load."""
        authenticated_client.force_login(driver)
        response = authenticated_client.get(
            reverse("covoiturage:edit_voyage", args=[voyage.id])
        )
        assert response.status_code == 200

    def test_delete_voyage_removes_voyage(self, authenticated_client, voyage, driver):
        """Deleting voyage should remove it."""
        authenticated_client.force_login(driver)
        response = authenticated_client.post(
            reverse("covoiturage:delete_voyage", args=[voyage.id]), {"confirm": True}
        )
        assert response.status_code == 302
        assert not Voyage.objects.filter(id=voyage.id).exists()

    def test_cannot_edit_others_voyage(self, authenticated_client, voyage):
        """User cannot edit another user's voyage."""
        response = authenticated_client.get(
            reverse("covoiturage:edit_voyage", args=[voyage.id])
        )
        # custom_404 redirects authenticated users to dashboard
        assert response.status_code in (302, 404)


@pytest.mark.django_db
class TestDemandeViews:
    """Tests for demande CRUD operations."""

    def test_add_demande_page_loads(self, authenticated_client):
        """Add demande page should load."""
        response = authenticated_client.get(reverse("covoiturage:add_demande"))
        assert response.status_code == 200

    def test_add_demande_creates_demande(self, authenticated_client):
        """Adding demande should create new demande."""
        data = {
            "ville_depart": "Kribi",
            "ville_arrivee": "Douala",
            "date_voyage": (timezone.now().date() + timedelta(days=3)).strftime(
                "%Y-%m-%d"
            ),
            "places": 2,
        }
        response = authenticated_client.post(reverse("covoiturage:add_demande"), data)
        assert response.status_code == 302
        assert Demande.objects.filter(ville_depart="Kribi").exists()


@pytest.mark.django_db
class TestSearch:
    """Tests for search functionality."""

    def test_search_page_loads(self, authenticated_client):
        """Search page should load."""
        response = authenticated_client.get(reverse("covoiturage:search_trajets"))
        assert response.status_code == 200

    def test_search_filters_work(self, authenticated_client, voyage):
        """Search filters should work correctly."""
        response = authenticated_client.get(
            reverse("covoiturage:search_trajets"),
            {"ville_depart": "Douala", "ville_arrivee": "Yaoundé"},
        )
        assert response.status_code == 200
        assert "voyages" in response.context

    def test_search_excludes_completed(self, authenticated_client, completed_voyage):
        """Completed voyages should not appear in search."""
        response = authenticated_client.get(reverse("covoiturage:search_trajets"))
        voyages = response.context["voyages"]
        assert completed_voyage not in [v for v in voyages.object_list]


@pytest.mark.django_db
class TestCorrespondanceViews:
    """Tests for correspondance operations."""

    def test_validate_correspondance(
        self, authenticated_client, correspondance, driver
    ):
        """Driver should be able to validate correspondance."""
        authenticated_client.force_login(driver)
        response = authenticated_client.post(
            reverse("covoiturage:validate_correspondance", args=[correspondance.id])
        )
        assert response.status_code == 302
        correspondance.refresh_from_db()
        assert correspondance.is_validated == True

    def test_refuse_correspondance(self, authenticated_client, correspondance, driver):
        """Driver should be able to refuse correspondance."""
        authenticated_client.force_login(driver)
        response = authenticated_client.post(
            reverse("covoiturage:refuse_correspondance", args=[correspondance.id])
        )
        assert response.status_code == 302
        correspondance.refresh_from_db()
        assert correspondance.refus_conducteur == True

    def test_cancel_correspondance(self, authenticated_client, correspondance, user):
        """Passager should be able to cancel correspondance."""
        authenticated_client.force_login(user)
        response = authenticated_client.post(
            reverse("covoiturage:cancel_correspondance", args=[correspondance.id])
        )
        assert response.status_code == 302
        correspondance.refresh_from_db()
        assert correspondance.refus_passager == True


@pytest.mark.django_db
class TestNotifications:
    """Tests for notification views."""

    def test_notifications_list_loads(self, authenticated_client):
        """Notifications list should load."""
        response = authenticated_client.get(reverse("covoiturage:notifications_list"))
        assert response.status_code == 200

    def test_mark_notification_read(self, authenticated_client, user):
        """Marking notification as read should work."""
        notification = Notification.objects.create(
            user=user,
            notification_type="match",
            title="Test notification",
            message="Test message",
        )
        response = authenticated_client.get(
            reverse("covoiturage:notifications_mark_read", args=[notification.id])
        )
        assert response.status_code == 302
        notification.refresh_from_db()
        assert notification.is_read == True


@pytest.mark.django_db
class TestFormValidation:
    """Tests for form validation in views."""

    def test_voyage_past_date_rejected(self, authenticated_client):
        """Voyage with past date should be rejected."""
        data = {
            "ville_depart": "City A",
            "ville_arrivee": "City B",
            "date_depart": (timezone.now() - timedelta(days=1)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "date_arrivee": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            "places_disponibles": 1,
            "prix_par_place": 1000,
            "plaque_immatriculation": "XX 0000 XX",
            "modele_voiture": "Test",
            "type_bagage_accepte": "moyen",
        }
        response = authenticated_client.post(reverse("covoiturage:add_voyage"), data)
        assert response.status_code == 200

    def test_demande_past_date_rejected(self, authenticated_client):
        """Demande with past date should be rejected."""
        data = {
            "ville_depart": "City A",
            "ville_arrivee": "City B",
            "date_voyage": (timezone.now().date() - timedelta(days=1)).strftime(
                "%Y-%m-%d"
            ),
            "places": 1,
        }
        response = authenticated_client.post(reverse("covoiturage:add_demande"), data)
        assert response.status_code == 200
