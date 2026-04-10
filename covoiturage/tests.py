from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from .models import Profile, Voyage, Demande, Correspondance, Avis, Message


class ProfileSignalTests(TestCase):
    """Auto-creation of Profile when a User is created."""

    def test_profile_created_on_user_creation(self):
        user = User.objects.create_user('alice', password='testpass123')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_has_default_trust_score(self):
        user = User.objects.create_user('bob', password='testpass123')
        self.assertEqual(user.profile.trust_score, 50)


class MatchingAlgorithmTests(TestCase):
    """Test the automatic matching between Voyages and Demandes."""

    def setUp(self):
        self.driver = User.objects.create_user('driver', password='testpass123')
        self.passenger = User.objects.create_user('passenger', password='testpass123')
        self.tomorrow = timezone.now() + timedelta(days=1)

    def test_exact_match_creates_correspondance(self):
        voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=3,
        )
        demande = Demande.objects.create(
            passager=self.passenger,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_voyage=self.tomorrow.date(), places=1,
        )
        self.assertTrue(Correspondance.objects.filter(voyage=voyage, demande=demande).exists())

    def test_case_insensitive_matching(self):
        voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='douala', ville_arrivee='yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=3,
        )
        demande = Demande.objects.create(
            passager=self.passenger,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_voyage=self.tomorrow.date(), places=1,
        )
        self.assertTrue(Correspondance.objects.filter(voyage=voyage, demande=demande).exists())

    def test_date_window_plus_one_day(self):
        voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=3,
        )
        demande = Demande.objects.create(
            passager=self.passenger,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_voyage=self.tomorrow.date() + timedelta(days=1), places=1,
        )
        match = Correspondance.objects.filter(voyage=voyage, demande=demande).first()
        self.assertIsNotNone(match)
        self.assertLess(match.score_match, 1.0)  # reduced score for +1 day

    def test_no_match_different_cities(self):
        voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=3,
        )
        Demande.objects.create(
            passager=self.passenger,
            ville_depart='Bamenda', ville_arrivee='Yaoundé',
            date_voyage=self.tomorrow.date(), places=1,
        )
        self.assertEqual(Correspondance.objects.count(), 0)

    def test_no_self_match(self):
        voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=3,
        )
        Demande.objects.create(
            passager=self.driver,  # same user
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_voyage=self.tomorrow.date(), places=1,
        )
        self.assertEqual(Correspondance.objects.count(), 0)

    def test_not_enough_places(self):
        voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=1,
        )
        Demande.objects.create(
            passager=self.passenger,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_voyage=self.tomorrow.date(), places=3,
        )
        self.assertEqual(Correspondance.objects.count(), 0)


class TrustScoreTests(TestCase):
    """Trust score is recalculated when a review is submitted."""

    def setUp(self):
        self.driver = User.objects.create_user('driver', password='testpass123')
        self.passenger = User.objects.create_user('passenger', password='testpass123')
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=3, est_termine=True,
        )

    def test_five_star_review_increases_trust(self):
        Avis.objects.create(
            voyage=self.voyage, auteur=self.passenger,
            utilisateur_note=self.driver, note=5,
        )
        self.driver.profile.refresh_from_db()
        self.assertEqual(self.driver.profile.trust_score, 70)  # 50 + (5-3)*10

    def test_one_star_review_decreases_trust(self):
        Avis.objects.create(
            voyage=self.voyage, auteur=self.passenger,
            utilisateur_note=self.driver, note=1,
        )
        self.driver.profile.refresh_from_db()
        self.assertEqual(self.driver.profile.trust_score, 30)  # 50 + (1-3)*10


class ViewAccessTests(TestCase):
    """Test view access control."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', password='testpass123')

    def test_landing_accessible_anonymous(self):
        resp = self.client.get(reverse('covoiturage:landing'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse('covoiturage:dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_accessible_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        resp = self.client.get(reverse('covoiturage:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_search_requires_login(self):
        resp = self.client.get(reverse('covoiturage:search_trajets'))
        self.assertEqual(resp.status_code, 302)

    def test_register_page_accessible(self):
        resp = self.client.get(reverse('covoiturage:register'))
        self.assertEqual(resp.status_code, 200)


class MessageTests(TestCase):
    """Test the messaging system."""

    def setUp(self):
        self.driver = User.objects.create_user('driver', password='testpass123')
        self.passenger = User.objects.create_user('passenger', password='testpass123')
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.voyage = Voyage.objects.create(
            conducteur=self.driver,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_depart=self.tomorrow, date_arrivee=self.tomorrow + timedelta(hours=4),
            places_disponibles=3,
        )
        self.demande = Demande.objects.create(
            passager=self.passenger,
            ville_depart='Douala', ville_arrivee='Yaoundé',
            date_voyage=self.tomorrow.date(), places=1,
        )
        self.correspondance = Correspondance.objects.get(
            voyage=self.voyage, demande=self.demande,
        )
        self.correspondance.is_validated = True
        self.correspondance.save()

    def test_conversation_requires_validation(self):
        self.correspondance.is_validated = False
        self.correspondance.save()
        self.client.login(username='driver', password='testpass123')
        resp = self.client.get(reverse('covoiturage:conversation', args=[self.correspondance.id]))
        self.assertEqual(resp.status_code, 302)  # redirect to dashboard

    def test_conversation_accessible_by_driver(self):
        self.client.login(username='driver', password='testpass123')
        resp = self.client.get(reverse('covoiturage:conversation', args=[self.correspondance.id]))
        self.assertEqual(resp.status_code, 200)

    def test_conversation_accessible_by_passenger(self):
        self.client.login(username='passenger', password='testpass123')
        resp = self.client.get(reverse('covoiturage:conversation', args=[self.correspondance.id]))
        self.assertEqual(resp.status_code, 200)

    def test_unrelated_user_blocked(self):
        outsider = User.objects.create_user('outsider', password='testpass123')
        self.client.login(username='outsider', password='testpass123')
        resp = self.client.get(reverse('covoiturage:conversation', args=[self.correspondance.id]))
        self.assertEqual(resp.status_code, 302)

    def test_send_message(self):
        self.client.login(username='driver', password='testpass123')
        resp = self.client.post(
            reverse('covoiturage:conversation', args=[self.correspondance.id]),
            {'content': 'Bonjour, je serai au rond-point à 8h.'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Message.objects.count(), 1)
        msg = Message.objects.first()
        self.assertEqual(msg.sender, self.driver)
        self.assertEqual(msg.correspondance, self.correspondance)
