"""
Management command to create demo/test accounts and data for pilots.
Usage: python manage.py create_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from covoiturage.models import Profile, Voyage, Demande, Correspondance
import random


class Command(BaseCommand):
    help = 'Create demo accounts and sample data for testing/pilots'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo accounts before creating new ones'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating demo data for pilot testing...'))

        if options['clear']:
            self.clear_demo_accounts()

        # Create demo driver
        driver = self.create_demo_user(
            username='demo_driver',
            email='driver@demo.test',
            password='DemoPass123!',
            first_name='Alain',
            last_name='Nsang',
            is_driver=True,
            phone='237674123456',
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Demo Driver: {driver.username} (same password)'))

        # Create demo passengers
        passengers = []
        passenger_data = [
            ('demo_passenger1', 'marie@demo.test', 'Marie', 'Onana', '237699456789'),
            ('demo_passenger2', 'jean@demo.test', 'Jean', 'Likwelele', '237670123456'),
            ('demo_passenger3', 'claire@demo.test', 'Claire', 'Tamwo', '237650987654'),
        ]

        for username, email, first_name, last_name, phone in passenger_data:
            passenger = self.create_demo_user(
                username=username,
                email=email,
                password='DemoPass123!',
                first_name=first_name,
                last_name=last_name,
                is_driver=False,
                phone=phone,
            )
            passengers.append(passenger)
            self.stdout.write(self.style.SUCCESS(f'✓ Demo Passenger: {passenger.username}'))

        # Create demo trips (voyages)
        self.stdout.write(self.style.WARNING('\n📍 Creating sample trips...'))
        trips = []

        trip_configs = [
            {
                'destination_from': 'Douala - Akwa',
                'pickup_point': 'Marché de Jamot',
                'destination_to': 'Limbe - Beach',
                'date_offset': 1,
                'seats': 3,
                'price': 3500,
                'accepts_momo': True,
                'accepts_cash': True,
            },
            {
                'destination_from': 'Yaoundé - Bastos',
                'pickup_point': 'Avenue Kennedy',
                'destination_to': 'Yaoundé - Mvogue',
                'date_offset': 2,
                'seats': 2,
                'price': 1500,
                'accepts_momo': True,
                'accepts_cash': False,
            },
            {
                'destination_from': 'Buea - Town',
                'pickup_point': 'Government School Junction',
                'destination_to': 'Buea - Molyko',
                'date_offset': 3,
                'seats': 4,
                'price': 2000,
                'accepts_momo': False,
                'accepts_cash': True,
            },
        ]

        for config in trip_configs:
            trip = Voyage.objects.create(
                conducteur=driver,
                ville_depart=config['destination_from'],
                lieu_ramassage=config['pickup_point'],
                ville_arrivee=config['destination_to'],
                date_depart=timezone.now() + timedelta(days=config['date_offset']),
                date_arrivee=timezone.now() + timedelta(days=config['date_offset'], hours=2),
                places_disponibles=config['seats'],
                prix_par_place=config['price'],
                currency='XAF',
                accept_mobile_money=config['accepts_momo'],
                accept_cash=config['accepts_cash'],
                plaque_immatriculation='CM-DEMO-001',
                modele_voiture='Toyota Corolla 2015',
                type_bagage_accepte='small,medium',
                women_only=False,
                est_termine=False,
            )
            trips.append(trip)
            self.stdout.write(self.style.SUCCESS(
                f'✓ Trip: {config["destination_from"]} → {config["destination_to"]} ({config["price"]} XAF)'
            ))

        # Create sample requests (demandes) from passengers
        self.stdout.write(self.style.WARNING('\n📋 Creating sample ride requests...'))
        for idx, passenger in enumerate(passengers):
            demande = Demande.objects.create(
                passager=passenger,
                ville_depart=trip_configs[idx % len(trip_configs)]['destination_from'],
                ville_arrivee=trip_configs[idx % len(trip_configs)]['destination_to'],
                date_voyage=(timezone.now() + timedelta(days=(idx % 3) + 1)).date(),  # Use .date() for date field
                places=random.randint(1, 3),
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Request from {passenger.username}'))

            # Auto-match some requests with available trips
            matching_trip = trips[idx % len(trips)]
            if matching_trip.places_disponibles > 0:
                corr = Correspondance.objects.create(
                    voyage=matching_trip,
                    demande=demande,
                    score_match=85 + random.randint(0, 15),
                    is_validated=False,
                )
                self.stdout.write(self.style.SUCCESS(f'  → Auto-matched with trip'))

        # Print demo credentials
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.WARNING('📱 DEMO CREDENTIALS FOR TESTING'))
        self.stdout.write('='*60)
        self.stdout.write(f'\nDRIVER:\n  Username: demo_driver\n  Password: DemoPass123!')
        self.stdout.write(f'\nPASSENGERS:')
        for username, email, _, _, _ in passenger_data:
            self.stdout.write(f'  Username: {username}\n  Password: DemoPass123!')
        self.stdout.write(f'\nDefault test login page: http://localhost:8000/login/\n')
        self.stdout.write('='*60)

    def create_demo_user(self, username, email, password, first_name, last_name, is_driver, phone):
        """Create a demo user with profile."""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        if created:
            user.set_password(password)
            user.save()

        # Create or update profile
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_driver = is_driver
        profile.phone = phone
        profile.phone_verified = True
        profile.bio = f'Demo {first_name} for testing' if is_driver else f'Demo passenger testing'
        profile.trust_score = 4.5
        profile.save()

        return user

    def clear_demo_accounts(self):
        """Delete demo accounts (optional)."""
        demo_usernames = [
            'demo_driver',
            'demo_passenger1',
            'demo_passenger2',
            'demo_passenger3',
        ]
        deleted, _ = User.objects.filter(username__in=demo_usernames).delete()
        self.stdout.write(self.style.WARNING(f'🗑️  Cleared {deleted} demo accounts'))
