"""Tests for the public shareable trip page (WhatsApp distribution)."""

from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from covoiturage.models import Voyage


@pytest.mark.django_db
def test_public_trip_page_renders_for_valid_trip(voyage):
    res = Client().get(reverse("covoiturage:public_voyage", args=[voyage.id]))
    assert res.status_code == 200
    body = res.content.decode()
    assert voyage.ville_depart in body and voyage.ville_arrivee in body


@pytest.mark.django_db
def test_public_trip_page_404_for_completed(driver):
    dt = timezone.now() + timedelta(days=1)
    v = Voyage.objects.create(
        conducteur=driver, ville_depart="Douala", ville_arrivee="Yaoundé",
        date_depart=dt, date_arrivee=dt + timedelta(hours=3),
        places_disponibles=2, prix_par_place=3000, est_termine=True,
    )
    res = Client().get(reverse("covoiturage:public_voyage", args=[v.id]))
    assert res.status_code == 404


@pytest.mark.django_db
def test_public_trip_page_404_for_missing():
    res = Client().get(reverse("covoiturage:public_voyage", args=[999999]))
    assert res.status_code == 404


@pytest.mark.django_db
def test_public_trip_page_is_anonymous(voyage):
    # No login redirect — must be reachable by anonymous visitors (WhatsApp click).
    res = Client().get(reverse("covoiturage:public_voyage", args=[voyage.id]))
    assert res.status_code == 200
