"""Tests for the Trust & Safety bundle: women-only matching/visibility and SOS/share."""

from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from covoiturage.models import Voyage, Demande, Correspondance
from covoiturage.services import matching, safety
from covoiturage.services.trips import search_voyages
from covoiturage.messaging_gateway.console import ConsoleGateway


@pytest.fixture(autouse=True)
def _reset_sms():
    ConsoleGateway.reset()
    yield
    ConsoleGateway.reset()


def _female(user):
    user.profile.gender = "female"
    user.profile.save()
    return user


def _women_only_voyage(driver):
    _female(driver)
    dt = timezone.now() + timedelta(days=1)
    return Voyage.objects.create(
        conducteur=driver, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_depart=dt, date_arrivee=dt + timedelta(hours=4),
        places_disponibles=3, prix_par_place=5000, women_only=True,
    )


def _demande(passenger, day_offset=1):
    return Demande.objects.create(
        passager=passenger, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_voyage=(timezone.now() + timedelta(days=day_offset)).date(), places=1,
    )


@pytest.mark.django_db
def test_women_only_matches_female_passenger(driver, user):
    voyage = _women_only_voyage(driver)
    _female(user)
    assert matching.compute_match_score(voyage, _demande(user)) > 0


@pytest.mark.django_db
def test_women_only_does_not_match_male(driver, user):
    voyage = _women_only_voyage(driver)
    user.profile.gender = "male"
    user.profile.save()
    assert matching.compute_match_score(voyage, _demande(user)) == 0.0


@pytest.mark.django_db
def test_women_only_hidden_from_men_in_search(driver, user):
    _women_only_voyage(driver)
    user.profile.gender = "male"
    user.profile.save()
    assert not search_voyages({}, user=user).filter(women_only=True).exists()


@pytest.mark.django_db
def test_women_only_visible_to_women_in_search(driver, user):
    _women_only_voyage(driver)
    _female(user)
    assert search_voyages({}, user=user).filter(women_only=True).exists()


@pytest.mark.django_db
def test_women_only_hidden_from_anonymous(driver):
    _women_only_voyage(driver)
    assert not search_voyages({}, user=None).filter(women_only=True).exists()


# ── SOS / share ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_share_requires_emergency_contact(user, completed_voyage):
    corr = Correspondance.objects.get(voyage=completed_voyage)
    with pytest.raises(safety.SafetyError):
        safety.share_trip(corr, user)


@pytest.mark.django_db
def test_share_sms_goes_to_emergency_contact(user, completed_voyage):
    user.profile.emergency_contact_phone = "+237650000000"
    user.profile.save()
    corr = Correspondance.objects.get(voyage=completed_voyage)
    phone = safety.share_trip(corr, user)
    assert phone == "+237650000000"
    assert any(to == "+237650000000" for to, _ in ConsoleGateway.sent)


@pytest.mark.django_db
def test_sos_sms_is_urgent(user, completed_voyage):
    user.profile.emergency_contact_phone = "+237650000000"
    user.profile.save()
    corr = Correspondance.objects.get(voyage=completed_voyage)
    safety.sos(corr, user)
    assert any("URGENCE" in text for _, text in ConsoleGateway.sent)


@pytest.mark.django_db
def test_non_participant_cannot_share(user2, completed_voyage):
    user2.profile.emergency_contact_phone = "+237651111111"
    user2.profile.save()
    corr = Correspondance.objects.get(voyage=completed_voyage)
    with pytest.raises(safety.SafetyError):
        safety.share_trip(corr, user2)


@pytest.mark.django_db
def test_trip_token_roundtrip(completed_voyage):
    corr = Correspondance.objects.get(voyage=completed_voyage)
    token = safety.make_trip_token(corr)
    assert safety.read_trip_token(token) == corr.id
    assert safety.read_trip_token("garbage") is None
