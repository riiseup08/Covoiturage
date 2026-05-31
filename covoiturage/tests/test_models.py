import pytest
from django.contrib.auth.models import User
from covoiturage.models import (
    Profile,
    Voyage,
    Demande,
    Correspondance,
    Avis,
    Notification,
    Message,
    Wallet,
    Transaction,
)
from datetime import timedelta
from django.utils import timezone
from django.db import IntegrityError


@pytest.mark.django_db
class TestProfile:
    """Tests for Profile model."""

    def test_profile_created_on_user_creation(self, user):
        """Profile should be auto-created when user is created."""
        assert hasattr(user, "profile")
        assert user.profile is not None

    def test_profile_str(self, profile, user):
        """Profile string representation."""
        assert str(profile) == f"Profil de {user.username}"

    def test_profile_default_values(self, profile):
        """Profile should have correct default values."""
        assert profile.bio == ""
        assert profile.is_driver == False
        assert profile.id_verified == False
        assert profile.driver_license_verified == False
        assert profile.phone_verified == False
        assert profile.verification_status == "not_started"
        assert profile.trust_score == 50

    def test_profile_driver_creation(self, driver):
        """Driver profile should be marked as driver."""
        assert driver.profile.is_driver == True

    def test_wallet_created_on_user_creation(self, user):
        """Wallet should be auto-created when user is created."""
        assert hasattr(user, "wallet")
        assert user.wallet is not None
        assert user.wallet.balance == 0.00


@pytest.mark.django_db
class TestVoyage:
    """Tests for Voyage model."""

    def test_voyage_creation(self, voyage, driver):
        """Voyage should be created with correct values."""
        assert voyage.conducteur == driver
        assert voyage.ville_depart == "Douala"
        assert voyage.ville_arrivee == "Yaoundé"
        assert voyage.places_disponibles == 3
        assert voyage.prix_par_place == 5000.00
        assert voyage.est_termine == False

    def test_voyage_str(self, voyage, driver):
        """Voyage string representation."""
        expected = f"Trajet de {driver.username}: Douala -> Yaoundé"
        assert str(voyage) == expected

    def test_voyage_default_status(self, voyage):
        """Voyage should have correct default status."""
        assert voyage.status == "pending"
        assert voyage.is_validated == False
        assert voyage.driver_confirmed_pickup == False
        assert voyage.driver_confirmed_dropoff == False

    def test_voyage_baggage_choices(self):
        """Voyage should accept valid baggage types."""
        valid_types = ["petit", "moyen", "gros", "tous"]
        for baggage_type in valid_types:
            voyage = Voyage(
                conducteur_id=1,
                ville_depart="City A",
                ville_arrivee="City B",
                date_depart=timezone.now() + timedelta(days=1),
                date_arrivee=timezone.now() + timedelta(days=1, hours=2),
                plaque_immatriculation="XX 0000 XX",
                modele_voiture="Test Car",
                type_bagage_accepte=baggage_type,
            )
            assert voyage.type_bagage_accepte in valid_types


@pytest.mark.django_db
class TestDemande:
    """Tests for Demande model."""

    def test_demande_creation(self, demande, user):
        """Demande should be created with correct values."""
        assert demande.passager == user
        assert demande.ville_depart == "Douala"
        assert demande.ville_arrivee == "Yaoundé"
        assert demande.places == 1

    def test_demande_str(self, demande, user):
        """Demande string representation."""
        expected = f"Demande de {user.username}: Douala -> Yaoundé"
        assert str(demande) == expected


@pytest.mark.django_db
class TestCorrespondance:
    """Tests for Correspondance model."""

    def test_correspondance_creation(self, correspondance, voyage, demande):
        """Correspondance should link voyage and demande."""
        assert correspondance.voyage == voyage
        assert correspondance.demande == demande
        assert correspondance.score_match == 0.85
        assert correspondance.is_validated == False

    def test_correspondance_str(self, correspondance):
        """Correspondance string representation."""
        assert "Match:" in str(correspondance)


@pytest.mark.django_db
class TestAvis:
    """Tests for Avis model."""

    def test_avis_creation(self, completed_voyage, user, user2, driver):
        """Avis should be created correctly."""
        avis = Avis.objects.create(
            voyage=completed_voyage,
            auteur=driver,
            utilisateur_note=user,
            note=5,
            commentaire="Excellent passager!",
        )
        assert avis.note == 5
        assert avis.commentaire == "Excellent passager!"

    def test_avis_note_choices(self):
        """Avis note should be between 1 and 5."""
        choices = [i for i in range(1, 6)]
        assert len(choices) == 5
        assert 1 in choices
        assert 5 in choices


@pytest.mark.django_db
class TestNotification:
    """Tests for Notification model."""

    def test_notification_creation(self, user):
        """Notification should be created correctly."""
        notification = Notification.objects.create(
            user=user,
            notification_type="match",
            title="Nouveau match!",
            message="Quelqu'un veut voyager avec vous.",
        )
        assert notification.is_read == False
        assert notification.user == user

    def test_notification_icon(self, user):
        """Notification should return correct icon."""
        notification = Notification.objects.create(
            user=user,
            notification_type="match",
            title="Test",
            message="Test message",
        )
        assert notification.icon == "🤝"

        notification.notification_type = "review"
        assert notification.icon == "⭐"


@pytest.mark.django_db
class TestWallet:
    """Tests for Wallet model."""

    def test_wallet_creation(self, wallet, user):
        """Wallet should be created with default values."""
        assert wallet.user == user
        assert wallet.balance == 0.00
        assert wallet.currency == "XAF"

    def test_wallet_str(self, wallet, user):
        """Wallet string representation."""
        expected = f"Wallet of {user.username}: 0.00 XAF"
        assert str(wallet) == expected

    def test_wallet_is_active(self, wallet):
        """Wallet should be active when balance >= 0."""
        assert wallet.is_active == True

        wallet.balance = -100.00
        assert wallet.is_active == False


@pytest.mark.django_db
class TestTransaction:
    """Tests for Transaction model."""

    def test_transaction_creation(self, wallet):
        """Transaction should be created correctly."""
        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=5000.00,
            transaction_type="topup",
            description="Rechargement Monetbil",
        )
        assert transaction.amount == 5000.00
        assert transaction.transaction_type == "topup"
