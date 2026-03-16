from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile, Voyage, Demande, Correspondance, Avis
from .forms import UserRegistrationForm, VoyageForm, DemandeForm, ProfileForm
import datetime
from django.utils import timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username='user1', password='TestPass123!', email=None):
    email = email or f'{username}@test.com'
    return User.objects.create_user(username=username, email=email, password=password)


def make_voyage(conducteur, days_ahead=1, **kwargs):
    defaults = dict(
        conducteur=conducteur,
        ville_depart='Douala',
        ville_arrivee='Yaoundé',
        date_depart=timezone.now() + datetime.timedelta(days=days_ahead),
        date_arrivee=timezone.now() + datetime.timedelta(days=days_ahead, hours=4),
        places_disponibles=3,
        prix_par_place=5000,
        plaque_immatriculation='AB 1234 CD',
        modele_voiture='Toyota Corolla',
    )
    defaults.update(kwargs)
    return Voyage.objects.create(**defaults)


def make_demande(passager, days_ahead=1, **kwargs):
    defaults = dict(
        passager=passager,
        ville_depart='Douala',
        ville_arrivee='Yaoundé',
        date_voyage=(timezone.now() + datetime.timedelta(days=days_ahead)).date(),
        places=1,
    )
    defaults.update(kwargs)
    return Demande.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Registration form
# ---------------------------------------------------------------------------

class UserRegistrationFormTest(TestCase):
    """Tests for email-based user registration form."""

    def test_valid_registration(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='existing', email='dup@example.com', password='pass')
        form_data = {
            'username': 'newuser',
            'email': 'dup@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_required(self):
        form_data = {
            'username': 'testuser',
            'email': '',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_saved_lowercase(self):
        form_data = {
            'username': 'caseuser',
            'email': 'UPPER@EXAMPLE.COM',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, 'upper@example.com')


# ---------------------------------------------------------------------------
# Profile photo field
# ---------------------------------------------------------------------------

class ProfilePhotoFieldTest(TestCase):
    """Tests that Profile model has photo_profil field."""

    def test_profile_created_on_user_save(self):
        user = make_user('photousr')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_photo_field_exists(self):
        user = make_user('photousr2')
        profile = Profile.objects.get(user=user)
        self.assertFalse(bool(profile.photo_profil))

    def test_profile_str(self):
        user = make_user('struser')
        profile = Profile.objects.get(user=user)
        self.assertIn('struser', str(profile))


# ---------------------------------------------------------------------------
# Voyage photo field
# ---------------------------------------------------------------------------

class VoyagePhotoFieldTest(TestCase):
    """Tests that Voyage model has photo_vehicule field."""

    def test_voyage_photo_field_exists(self):
        user = make_user('driver')
        voyage = make_voyage(user)
        self.assertFalse(bool(voyage.photo_vehicule))

    def test_voyage_str(self):
        user = make_user('driver2')
        voyage = make_voyage(user)
        self.assertIn('Douala', str(voyage))


# ---------------------------------------------------------------------------
# Registration view
# ---------------------------------------------------------------------------

class RegisterViewTest(TestCase):

    def test_register_page_loads(self):
        response = self.client.get(reverse('covoiturage:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email')

    def test_register_post_creates_user(self):
        response = self.client.post(reverse('covoiturage:register'), {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_redirects_to_dashboard(self):
        response = self.client.post(reverse('covoiturage:register'), {
            'username': 'redir',
            'email': 'redir@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }, follow=True)
        self.assertRedirects(response, reverse('covoiturage:dashboard'))

    def test_register_invalid_no_redirect(self):
        response = self.client.post(reverse('covoiturage:register'), {
            'username': '',
            'email': 'bad',
            'password1': 'x',
            'password2': 'y',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='bad').exists())


# ---------------------------------------------------------------------------
# Login view
# ---------------------------------------------------------------------------

class LoginViewTest(TestCase):

    def setUp(self):
        self.user = make_user('loginuser', email='login@test.com')

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_with_username(self):
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_with_email(self):
        response = self.client.post(reverse('login'), {
            'username': 'login@test.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_wrong_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

class LandingViewTest(TestCase):

    def test_landing_loads(self):
        response = self.client.get(reverse('covoiturage:landing'))
        self.assertEqual(response.status_code, 200)

    def test_landing_contains_brand(self):
        response = self.client.get(reverse('covoiturage:landing'))
        self.assertContains(response, 'AFRICA', msg_prefix='Landing page should mention AFRICA')

    def test_landing_contains_register_link(self):
        response = self.client.get(reverse('covoiturage:landing'))
        self.assertContains(response, reverse('covoiturage:register'))


# ---------------------------------------------------------------------------
# Dashboard (requires login)
# ---------------------------------------------------------------------------

class DashboardViewTest(TestCase):

    def setUp(self):
        self.user = make_user('dashuser')
        self.client.login(username='dashuser', password='TestPass123!')

    def test_dashboard_loads(self):
        response = self.client.get(reverse('covoiturage:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.get(reverse('covoiturage:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_dashboard_shows_user_voyages(self):
        voyage = make_voyage(self.user)
        response = self.client.get(reverse('covoiturage:dashboard'))
        self.assertContains(response, voyage.ville_depart)

    def test_dashboard_shows_user_demandes(self):
        demande = make_demande(self.user)
        response = self.client.get(reverse('covoiturage:dashboard'))
        self.assertContains(response, demande.ville_depart)


# ---------------------------------------------------------------------------
# Voyage CRUD
# ---------------------------------------------------------------------------

class VoyageFormTest(TestCase):

    def setUp(self):
        self.user = make_user('formdriver')
        self.client.login(username='formdriver', password='TestPass123!')

    def test_add_voyage_page_loads(self):
        response = self.client.get(reverse('covoiturage:add_voyage'))
        self.assertEqual(response.status_code, 200)

    def test_add_voyage_valid_post(self):
        future = timezone.now() + datetime.timedelta(days=2)
        later = future + datetime.timedelta(hours=3)
        response = self.client.post(reverse('covoiturage:add_voyage'), {
            'ville_depart': 'Douala',
            'lieu_ramassage': 'Gare routière',
            'ville_arrivee': 'Yaoundé',
            'date_depart': future.strftime('%Y-%m-%dT%H:%M'),
            'date_arrivee': later.strftime('%Y-%m-%dT%H:%M'),
            'places_disponibles': 3,
            'prix_par_place': '5000',
            'plaque_immatriculation': 'AB 1234',
            'modele_voiture': 'Toyota Corolla',
            'type_bagage_accepte': 'moyen',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Voyage.objects.filter(conducteur=self.user, ville_depart='Douala').exists())

    def test_add_voyage_invalid_past_date(self):
        past = timezone.now() - datetime.timedelta(days=1)
        later = past + datetime.timedelta(hours=3)
        response = self.client.post(reverse('covoiturage:add_voyage'), {
            'ville_depart': 'Douala',
            'ville_arrivee': 'Yaoundé',
            'date_depart': past.strftime('%Y-%m-%dT%H:%M'),
            'date_arrivee': later.strftime('%Y-%m-%dT%H:%M'),
            'places_disponibles': 2,
            'prix_par_place': '3000',
            'plaque_immatriculation': 'AB 1234',
            'modele_voiture': 'Toyota',
            'type_bagage_accepte': 'moyen',
        })
        self.assertEqual(response.status_code, 200)  # form error, stay on page

    def test_edit_voyage_page_loads(self):
        voyage = make_voyage(self.user)
        response = self.client.get(reverse('covoiturage:edit_voyage', args=[voyage.id]))
        self.assertEqual(response.status_code, 200)

    def test_edit_voyage_other_user_forbidden(self):
        other = make_user('otherdrv')
        voyage = make_voyage(other)
        # custom_404 redirects authenticated users to dashboard instead of showing 404
        response = self.client.get(reverse('covoiturage:edit_voyage', args=[voyage.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response['Location'])

    def test_delete_voyage_page_loads(self):
        voyage = make_voyage(self.user)
        response = self.client.get(reverse('covoiturage:delete_voyage', args=[voyage.id]))
        self.assertEqual(response.status_code, 200)

    def test_delete_voyage_post(self):
        voyage = make_voyage(self.user)
        response = self.client.post(reverse('covoiturage:delete_voyage', args=[voyage.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Voyage.objects.filter(id=voyage.id).exists())


# ---------------------------------------------------------------------------
# Demande CRUD
# ---------------------------------------------------------------------------

class DemandeViewTest(TestCase):

    def setUp(self):
        self.user = make_user('passengerA')
        self.client.login(username='passengerA', password='TestPass123!')

    def test_add_demande_page_loads(self):
        response = self.client.get(reverse('covoiturage:add_demande'))
        self.assertEqual(response.status_code, 200)

    def test_add_demande_valid_post(self):
        future = (timezone.now() + datetime.timedelta(days=1)).date()
        response = self.client.post(reverse('covoiturage:add_demande'), {
            'ville_depart': 'Bafoussam',
            'ville_arrivee': 'Douala',
            'date_voyage': future.strftime('%Y-%m-%d'),
            'places': 2,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Demande.objects.filter(passager=self.user, ville_depart='Bafoussam').exists())

    def test_add_demande_past_date_rejected(self):
        past = (timezone.now() - datetime.timedelta(days=1)).date()
        response = self.client.post(reverse('covoiturage:add_demande'), {
            'ville_depart': 'Bafoussam',
            'ville_arrivee': 'Douala',
            'date_voyage': past.strftime('%Y-%m-%d'),
            'places': 1,
        })
        self.assertEqual(response.status_code, 200)

    def test_edit_demande_page_loads(self):
        demande = make_demande(self.user)
        response = self.client.get(reverse('covoiturage:edit_demande', args=[demande.id]))
        self.assertEqual(response.status_code, 200)

    def test_edit_demande_other_user_forbidden(self):
        other = make_user('passengerB')
        demande = make_demande(other)
        # custom_404 redirects authenticated users to dashboard instead of showing 404
        response = self.client.get(reverse('covoiturage:edit_demande', args=[demande.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response['Location'])

    def test_delete_demande_post(self):
        demande = make_demande(self.user)
        response = self.client.post(reverse('covoiturage:delete_demande', args=[demande.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Demande.objects.filter(id=demande.id).exists())


# ---------------------------------------------------------------------------
# Search view
# ---------------------------------------------------------------------------

class SearchViewTest(TestCase):

    def setUp(self):
        self.user = make_user('searchusr')
        self.client.login(username='searchusr', password='TestPass123!')
        driver = make_user('driver_s', email='driver_s@test.com')
        self.voyage = make_voyage(driver)

    def test_search_page_loads(self):
        response = self.client.get(reverse('covoiturage:search_trajets'))
        self.assertEqual(response.status_code, 200)

    def test_search_finds_matching_voyage(self):
        response = self.client.get(reverse('covoiturage:search_trajets'), {
            'ville_depart': 'Douala',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Douala')

    def test_search_no_results_for_unknown_city(self):
        response = self.client.get(reverse('covoiturage:search_trajets'), {
            'ville_depart': 'CityThatDoesNotExist_XYZ',
        })
        self.assertEqual(response.status_code, 200)

    def test_search_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.get(reverse('covoiturage:search_trajets'))
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# Profile view
# ---------------------------------------------------------------------------

class ProfileViewTest(TestCase):

    def setUp(self):
        self.user = make_user('profileusr')
        self.client.login(username='profileusr', password='TestPass123!')

    def test_profile_page_loads(self):
        response = self.client.get(reverse('covoiturage:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        response = self.client.post(reverse('covoiturage:profile'), {
            'bio': 'Conducteur expérimenté',
            'phone': '+237600000001',
            'is_driver': True,
        })
        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.bio, 'Conducteur expérimenté')
        self.assertEqual(profile.phone, '+237600000001')
        self.assertTrue(profile.is_driver)

    def test_public_profile_loads(self):
        response = self.client.get(
            reverse('covoiturage:public_profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_public_profile_unknown_user_redirects(self):
        # custom_404 redirects authenticated users to dashboard instead of showing 404
        response = self.client.get(
            reverse('covoiturage:public_profile', kwargs={'username': 'ghostuser'})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response['Location'])


# ---------------------------------------------------------------------------
# Correspondance actions
# ---------------------------------------------------------------------------

class CorrespondanceActionsTest(TestCase):

    def setUp(self):
        self.driver = make_user('corrdriver', email='corrdriver@test.com')
        self.passenger = make_user('corrpass', email='corrpass@test.com')
        self.voyage = make_voyage(self.driver)
        self.demande = make_demande(self.passenger)
        self.corr = Correspondance.objects.create(
            voyage=self.voyage, demande=self.demande, score_match=1.0
        )

    def test_validate_correspondance(self):
        self.client.login(username='corrdriver', password='TestPass123!')
        response = self.client.post(
            reverse('covoiturage:validate_correspondance', args=[self.corr.id])
        )
        self.assertEqual(response.status_code, 302)
        self.corr.refresh_from_db()
        self.assertTrue(self.corr.is_validated)

    def test_refuse_correspondance(self):
        self.client.login(username='corrdriver', password='TestPass123!')
        response = self.client.post(
            reverse('covoiturage:refuse_correspondance', args=[self.corr.id])
        )
        self.assertEqual(response.status_code, 302)
        self.corr.refresh_from_db()
        self.assertTrue(self.corr.refus_conducteur)

    def test_cancel_correspondance_by_passenger(self):
        self.client.login(username='corrpass', password='TestPass123!')
        response = self.client.post(
            reverse('covoiturage:cancel_correspondance', args=[self.corr.id])
        )
        self.assertEqual(response.status_code, 302)
        self.corr.refresh_from_db()
        self.assertTrue(self.corr.refus_passager)

    def test_wrong_user_cannot_validate(self):
        self.client.login(username='corrpass', password='TestPass123!')
        # custom_404 redirects authenticated users to dashboard when resource not found
        response = self.client.post(
            reverse('covoiturage:validate_correspondance', args=[self.corr.id])
        )
        self.assertEqual(response.status_code, 302)
        # The correspondance should NOT be validated
        self.corr.refresh_from_db()
        self.assertFalse(self.corr.is_validated)


# ---------------------------------------------------------------------------
# Mark voyage as terminated
# ---------------------------------------------------------------------------

class MarkVoyageTermineTest(TestCase):

    def setUp(self):
        self.driver = make_user('termdriver')
        self.client.login(username='termdriver', password='TestPass123!')
        self.voyage = make_voyage(self.driver)

    def test_mark_voyage_termine(self):
        response = self.client.post(
            reverse('covoiturage:mark_voyage_termine', args=[self.voyage.id])
        )
        self.assertEqual(response.status_code, 302)
        self.voyage.refresh_from_db()
        self.assertTrue(self.voyage.est_termine)

    def test_terminated_voyage_hidden_from_search(self):
        self.voyage.est_termine = True
        self.voyage.save()
        response = self.client.get(reverse('covoiturage:search_trajets'), {
            'ville_depart': 'Douala',
        })
        # Voyage terminé ne devrait pas apparaître dans les résultats
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Avis (reviews)
# ---------------------------------------------------------------------------

class AvisViewTest(TestCase):

    def setUp(self):
        self.driver = make_user('avisdriver', email='avisdriver@test.com')
        self.passenger = make_user('avispass', email='avispass@test.com')
        self.voyage = make_voyage(self.driver, est_termine=True)
        self.demande = make_demande(self.passenger)
        self.corr = Correspondance.objects.create(
            voyage=self.voyage, demande=self.demande,
            score_match=1.0, is_validated=True
        )

    def test_avis_list_loads(self):
        self.client.login(username='avisdriver', password='TestPass123!')
        response = self.client.get(reverse('covoiturage:avis_list'))
        self.assertEqual(response.status_code, 200)

    def test_driver_can_leave_review_on_passenger(self):
        self.client.login(username='avisdriver', password='TestPass123!')
        response = self.client.post(
            reverse('covoiturage:add_avis', kwargs={
                'voyage_id': self.voyage.id,
                'user_id': self.passenger.id,
            }),
            {'note': 5, 'commentaire': 'Passager agréable'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Avis.objects.filter(
                auteur=self.driver,
                utilisateur_note=self.passenger,
                voyage=self.voyage,
            ).exists()
        )

    def test_cannot_review_self(self):
        self.client.login(username='avisdriver', password='TestPass123!')
        response = self.client.post(
            reverse('covoiturage:add_avis', kwargs={
                'voyage_id': self.voyage.id,
                'user_id': self.driver.id,
            }),
            {'note': 5, 'commentaire': 'Je me note moi-même'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Avis.objects.filter(auteur=self.driver, utilisateur_note=self.driver).exists()
        )

    def test_duplicate_review_blocked(self):
        Avis.objects.create(
            voyage=self.voyage, auteur=self.driver,
            utilisateur_note=self.passenger, note=4,
        )
        self.client.login(username='avisdriver', password='TestPass123!')
        response = self.client.post(
            reverse('covoiturage:add_avis', kwargs={
                'voyage_id': self.voyage.id,
                'user_id': self.passenger.id,
            }),
            {'note': 5, 'commentaire': 'Again'},
            follow=True,
        )
        self.assertEqual(Avis.objects.filter(
            auteur=self.driver, utilisateur_note=self.passenger
        ).count(), 1)


# ---------------------------------------------------------------------------
# Matching signal (auto-create Correspondance)
# ---------------------------------------------------------------------------

class MatchingSignalTest(TestCase):

    def test_voyage_creation_matches_existing_demande(self):
        driver = make_user('sigdrv', email='sigdrv@test.com')
        passenger = make_user('sigpass', email='sigpass@test.com')
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        demande = Demande.objects.create(
            passager=passenger,
            ville_depart='Kribi',
            ville_arrivee='Edea',
            date_voyage=tomorrow.date(),
            places=1,
        )
        voyage = Voyage.objects.create(
            conducteur=driver,
            ville_depart='Kribi',
            ville_arrivee='Edea',
            date_depart=tomorrow,
            date_arrivee=tomorrow + datetime.timedelta(hours=2),
            places_disponibles=2,
            prix_par_place=2000,
            plaque_immatriculation='CD 5678',
            modele_voiture='Honda Civic',
        )
        self.assertTrue(
            Correspondance.objects.filter(voyage=voyage, demande=demande).exists()
        )

    def test_demande_creation_matches_existing_voyage(self):
        driver = make_user('sigdrv2', email='sigdrv2@test.com')
        passenger = make_user('sigpass2', email='sigpass2@test.com')
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        voyage = Voyage.objects.create(
            conducteur=driver,
            ville_depart='Kribi',
            ville_arrivee='Edea',
            date_depart=tomorrow,
            date_arrivee=tomorrow + datetime.timedelta(hours=2),
            places_disponibles=3,
            prix_par_place=2000,
            plaque_immatriculation='EF 9012',
            modele_voiture='Nissan',
        )
        demande = Demande.objects.create(
            passager=passenger,
            ville_depart='Kribi',
            ville_arrivee='Edea',
            date_voyage=tomorrow.date(),
            places=1,
        )
        self.assertTrue(
            Correspondance.objects.filter(voyage=voyage, demande=demande).exists()
        )


# ---------------------------------------------------------------------------
# Authentication backend
# ---------------------------------------------------------------------------

class EmailOrUsernameBackendTest(TestCase):

    def setUp(self):
        self.user = make_user('backenduser', email='backend@test.com')

    def test_authenticate_by_username(self):
        from covoiturage.backends import EmailOrUsernameBackend
        backend = EmailOrUsernameBackend()
        user = backend.authenticate(None, username='backenduser', password='TestPass123!')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'backenduser')

    def test_authenticate_by_email(self):
        from covoiturage.backends import EmailOrUsernameBackend
        backend = EmailOrUsernameBackend()
        user = backend.authenticate(None, username='backend@test.com', password='TestPass123!')
        self.assertIsNotNone(user)

    def test_wrong_password_returns_none(self):
        from covoiturage.backends import EmailOrUsernameBackend
        backend = EmailOrUsernameBackend()
        user = backend.authenticate(None, username='backenduser', password='wrongpass')
        self.assertIsNone(user)

    def test_none_username_returns_none(self):
        from covoiturage.backends import EmailOrUsernameBackend
        backend = EmailOrUsernameBackend()
        user = backend.authenticate(None, username=None, password='TestPass123!')
        self.assertIsNone(user)
