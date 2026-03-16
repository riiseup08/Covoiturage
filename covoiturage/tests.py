from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile, Voyage
from .forms import UserRegistrationForm
import datetime
from django.utils import timezone


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


class ProfilePhotoFieldTest(TestCase):
    """Tests that Profile model has photo_profil field."""

    def test_profile_created_on_user_save(self):
        user = User.objects.create_user(username='photousr', password='pass')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_photo_field_exists(self):
        user = User.objects.create_user(username='photousr2', password='pass')
        profile = Profile.objects.get(user=user)
        # photo_profil should be blank by default
        self.assertFalse(bool(profile.photo_profil))


class VoyagePhotoFieldTest(TestCase):
    """Tests that Voyage model has photo_vehicule field."""

    def test_voyage_photo_field_exists(self):
        user = User.objects.create_user(username='driver', password='pass')
        voyage = Voyage.objects.create(
            conducteur=user,
            ville_depart='Douala',
            ville_arrivee='Yaoundé',
            date_depart=timezone.now() + datetime.timedelta(days=1),
            date_arrivee=timezone.now() + datetime.timedelta(days=1, hours=4),
            places_disponibles=3,
            prix_par_place=5000,
            plaque_immatriculation='AB 1234 CD',
            modele_voiture='Toyota Corolla',
        )
        # photo_vehicule should be blank by default
        self.assertFalse(bool(voyage.photo_vehicule))


class RegisterViewTest(TestCase):
    """Tests for the registration view."""

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


class LoginViewTest(TestCase):
    """Tests for the login view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', email='login@test.com', password='TestPass123!'
        )

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
