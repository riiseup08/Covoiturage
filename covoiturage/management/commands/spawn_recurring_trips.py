"""Materialize upcoming Voyage rows from active RecurringTrip templates.

Run daily (host cron / scheduler):  python manage.py spawn_recurring_trips
Idempotent — skips a template if its next-occurrence trip already exists.
"""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from covoiturage.models import RecurringTrip, Voyage
from covoiturage.services import trips


class Command(BaseCommand):
    help = "Create Voyage rows for the next occurrence of each active RecurringTrip."

    def add_arguments(self, parser):
        parser.add_argument(
            "--horizon-days", type=int, default=7,
            help="How many days ahead to materialize (default: 7).",
        )

    def handle(self, *args, **options):
        horizon = options["horizon_days"]
        today = timezone.localdate()
        created = 0

        for rt in RecurringTrip.objects.filter(active=True).select_related("conducteur"):
            for offset in range(horizon + 1):
                day = today + timedelta(days=offset)
                if day.weekday() != rt.weekday:
                    continue
                depart = timezone.make_aware(datetime.combine(day, rt.heure_depart))
                if depart < timezone.now():
                    continue
                # Idempotency: one trip per template per calendar day.
                exists = Voyage.objects.filter(
                    conducteur=rt.conducteur,
                    ville_depart=rt.ville_depart,
                    ville_arrivee=rt.ville_arrivee,
                    date_depart__date=day,
                ).exists()
                if exists:
                    continue
                trips.publish_voyage(
                    rt.conducteur,
                    ville_depart=rt.ville_depart,
                    lieu_ramassage=rt.lieu_ramassage,
                    ville_arrivee=rt.ville_arrivee,
                    date_depart=depart,
                    date_arrivee=depart + timedelta(minutes=rt.duree_minutes),
                    places_disponibles=rt.places_disponibles,
                    prix_par_place=rt.prix_par_place,
                    plaque_immatriculation=rt.plaque_immatriculation,
                    modele_voiture=rt.modele_voiture,
                    type_bagage_accepte=rt.type_bagage_accepte,
                    women_only=rt.women_only,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} trip(s)."))
