"""Tests for the USSD webhook and SMS notification fallback."""

from datetime import timedelta

import pytest
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from covoiturage.models import Voyage, Demande
from covoiturage.messaging_gateway.console import ConsoleGateway


@pytest.fixture(autouse=True)
def _reset_sms():
    ConsoleGateway.reset()
    yield
    ConsoleGateway.reset()


@pytest.fixture
def ussd_client():
    return Client()


def _post(client, text):
    return client.post(
        reverse("ussd_callback"),
        {"sessionId": "s1", "phoneNumber": "+237650000000", "text": text},
    )


@override_settings(USSD_ENABLED=True)
@pytest.mark.django_db
def test_ussd_main_menu(ussd_client):
    res = _post(ussd_client, "")
    body = res.content.decode()
    assert body.startswith("CON")
    assert "Publier" in body and "Chercher" in body


@override_settings(USSD_ENABLED=True)
@pytest.mark.django_db
def test_ussd_publish_creates_voyage(ussd_client):
    # 1 = publish, then ville_depart, ville_arrivee, date, prix
    res = _post(ussd_client, "1*Douala*Yaoundé*demain*5000")
    body = res.content.decode()
    assert body.startswith("END")
    assert Voyage.objects.filter(ville_depart="Douala", ville_arrivee="Yaoundé").exists()


@override_settings(USSD_ENABLED=True)
@pytest.mark.django_db
def test_ussd_search_lists_trips(ussd_client, driver):
    dt = timezone.now() + timedelta(days=1)
    Voyage.objects.create(
        conducteur=driver, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_depart=dt, date_arrivee=dt + timedelta(hours=4),
        places_disponibles=2, prix_par_place=4000,
    )
    res = _post(ussd_client, "2*Douala*Yaoundé")
    body = res.content.decode()
    assert body.startswith("END")
    assert "Trajets trouvés" in body


@override_settings(USSD_ENABLED=False)
@pytest.mark.django_db
def test_ussd_disabled_returns_404(ussd_client):
    res = _post(ussd_client, "")
    assert res.status_code == 404


@override_settings(USSD_ENABLED=True)
@pytest.mark.django_db
def test_match_sends_sms_to_feature_phone(driver, user):
    """When USSD is enabled, a new match notification also fans out over SMS."""
    # Give the passenger a phone so the SMS path fires.
    profile = user.profile
    profile.phone = "+237651111111"
    profile.save()

    dt = timezone.now() + timedelta(days=1)
    voyage = Voyage.objects.create(
        conducteur=driver, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_depart=dt, date_arrivee=dt + timedelta(hours=4),
        places_disponibles=2, prix_par_place=4000,
    )
    Demande.objects.create(
        passager=user, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_voyage=dt.date(), places=1,
    )
    # The post_save signal created a match -> notifications -> SMS.
    recipients = [to for (to, _text) in ConsoleGateway.sent]
    assert "+237651111111" in recipients
