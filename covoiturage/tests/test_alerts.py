"""Tests for saved-route alerts and recurring-trip materialization."""

from datetime import timedelta, time

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from covoiturage.models import Voyage, RouteAlert, RecurringTrip
from covoiturage.services import trips
from covoiturage.messaging_gateway.console import ConsoleGateway


@pytest.fixture(autouse=True)
def _reset_sms():
    ConsoleGateway.reset()
    yield
    ConsoleGateway.reset()


@override_settings(USSD_ENABLED=True)
@pytest.mark.django_db
def test_route_alert_notifies_on_matching_trip(driver, user):
    user.profile.phone = "+237650000000"
    user.profile.save()
    RouteAlert.objects.create(user=user, ville_depart="Douala", ville_arrivee="Yaoundé")

    dt = timezone.now() + timedelta(days=1)
    trips.publish_voyage(
        driver, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_depart=dt, date_arrivee=dt + timedelta(hours=4),
        places_disponibles=2, prix_par_place=4000,
    )
    # In-app notification created + SMS dispatched to the subscriber.
    assert user.notifications.filter(notification_type="match").exists()
    assert any(to == "+237650000000" for to, _ in ConsoleGateway.sent)


@pytest.mark.django_db
def test_route_alert_skips_driver_self(driver):
    RouteAlert.objects.create(user=driver, ville_depart="Douala", ville_arrivee="Yaoundé")
    dt = timezone.now() + timedelta(days=1)
    trips.publish_voyage(
        driver, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_depart=dt, date_arrivee=dt + timedelta(hours=4),
        places_disponibles=2, prix_par_place=4000,
    )
    assert not driver.notifications.filter(notification_type="match").exists()


@pytest.mark.django_db
def test_spawn_recurring_trips_creates_and_is_idempotent(driver):
    # A recurring trip for tomorrow's weekday.
    tomorrow = timezone.localdate() + timedelta(days=1)
    RecurringTrip.objects.create(
        conducteur=driver, ville_depart="Douala", ville_arrivee="Yaoundé",
        weekday=tomorrow.weekday(), heure_depart=time(8, 0),
        places_disponibles=3, prix_par_place=5000,
    )
    call_command("spawn_recurring_trips", "--horizon-days", "7")
    count_after_first = Voyage.objects.filter(conducteur=driver, date_depart__date=tomorrow).count()
    assert count_after_first == 1

    call_command("spawn_recurring_trips", "--horizon-days", "7")  # idempotent
    count_after_second = Voyage.objects.filter(conducteur=driver, date_depart__date=tomorrow).count()
    assert count_after_second == 1
