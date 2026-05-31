"""Tests for the endpoints the mobile client relies on (mine/termine/dashboard)."""

from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def client_as():
    def _make(user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c
    return _make


@pytest.mark.django_db
def test_voyages_mine_returns_only_own(client_as, driver, voyage):
    res = client_as(driver).get("/api/voyages/mine/")
    assert res.status_code == status.HTTP_200_OK
    results = res.json().get("results", res.json())
    assert all(v["conducteur"] == driver.id for v in results)
    assert any(v["id"] == voyage.id for v in results)


@pytest.mark.django_db
def test_voyages_mine_requires_auth():
    assert APIClient().get("/api/voyages/mine/").status_code in (401, 403)


@pytest.mark.django_db
def test_termine_marks_completed_and_returns_commission(client_as, driver, completed_voyage):
    completed_voyage.est_termine = False
    completed_voyage.save()
    res = client_as(driver).post(f"/api/voyages/{completed_voyage.id}/termine/")
    assert res.status_code == status.HTTP_200_OK
    completed_voyage.refresh_from_db()
    assert completed_voyage.est_termine is True
    # 3500 * 1 passenger * 10%
    assert Decimal(res.json()["commission"]) == Decimal("350.00")


@pytest.mark.django_db
def test_termine_forbidden_for_non_driver(client_as, user, voyage):
    res = client_as(user).post(f"/api/voyages/{voyage.id}/termine/")
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_dashboard_returns_counts(client_as, driver, voyage):
    res = client_as(driver).get("/api/dashboard/")
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["total_voyages"] >= 1
    assert {"total_demandes", "total_correspondances", "unread_count"} <= set(body)


@pytest.mark.django_db
def test_dashboard_requires_auth():
    assert APIClient().get("/api/dashboard/").status_code in (401, 403)
