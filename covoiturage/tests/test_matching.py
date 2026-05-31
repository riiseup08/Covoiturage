"""Tests for corridor matching in services/matching.py."""

from datetime import timedelta

import pytest
from django.utils import timezone

from covoiturage.models import Voyage, Demande, Correspondance
from covoiturage.services import matching

DOUALA = (4.0511, 9.7679)
YAOUNDE = (3.8480, 11.5021)
EDEA = (3.8000, 10.1333)
BAFOUSSAM = (5.4781, 10.4179)


def _voyage(driver, depart_in_days=1):
    dt = timezone.now() + timedelta(days=depart_in_days)
    return Voyage.objects.create(
        conducteur=driver,
        ville_depart="Douala",
        ville_arrivee="Yaoundé",
        date_depart=dt,
        date_arrivee=dt + timedelta(hours=4),
        places_disponibles=3,
        prix_par_place=5000,
        start_latitude=DOUALA[0], start_longitude=DOUALA[1],
        end_latitude=YAOUNDE[0], end_longitude=YAOUNDE[1],
    )


def _demande(passenger, start, end, depart_in_days=1, ville_depart="Douala", ville_arrivee="Edéa"):
    return Demande.objects.create(
        passager=passenger,
        ville_depart=ville_depart,
        ville_arrivee=ville_arrivee,
        date_voyage=(timezone.now() + timedelta(days=depart_in_days)).date(),
        places=1,
        start_latitude=start[0] if start else None,
        start_longitude=start[1] if start else None,
        end_latitude=end[0] if end else None,
        end_longitude=end[1] if end else None,
    )


@pytest.mark.django_db
def test_passenger_on_corridor_matches(driver, user):
    voyage = _voyage(driver)
    demande = _demande(user, DOUALA, EDEA)
    score = matching.compute_match_score(voyage, demande)
    assert score > 0


@pytest.mark.django_db
def test_passenger_off_corridor_does_not_match(driver, user):
    voyage = _voyage(driver)
    demande = _demande(user, DOUALA, BAFOUSSAM, ville_arrivee="Bafoussam")
    score = matching.compute_match_score(voyage, demande)
    assert score == 0.0


@pytest.mark.django_db
def test_city_fallback_when_no_coordinates(driver, user):
    """A demande without coordinates falls back to exact city matching (USSD path)."""
    voyage = _voyage(driver)
    demande = _demande(user, None, None, ville_arrivee="Yaoundé")
    score = matching.compute_match_score(voyage, demande)
    assert score > 0


@pytest.mark.django_db
def test_signal_creates_correspondance_for_corridor(driver, user):
    """Publishing a demande on the corridor auto-creates a match via the signal."""
    voyage = _voyage(driver)
    _demande(user, DOUALA, EDEA)
    assert Correspondance.objects.filter(voyage=voyage).exists()


@pytest.mark.django_db
def test_no_self_match(driver):
    voyage = _voyage(driver)
    demande = _demande(driver, DOUALA, EDEA)
    match = matching.try_create_match(voyage, demande)
    assert match is None
