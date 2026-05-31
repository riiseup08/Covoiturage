"""Regression tests proving the API authorization holes are closed.

Covers: IDOR on demandes, conversation membership on messages, review
participation rules, anonymous user enumeration, and PII (email/phone) leakage.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from covoiturage.models import Correspondance, Avis
from covoiturage.services.reviews import can_review


@pytest.fixture
def client_as():
    """Factory: an API client authenticated as the given user."""
    def _make(user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c
    return _make


# ── IDOR: demandes ──────────────────────────────────────────────────────
@pytest.mark.django_db
def test_cannot_patch_others_demande(client_as, user, user2, demande):
    res = client_as(user2).patch(f"/api/demandes/{demande.id}/", {"places": 9})
    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_cannot_delete_others_demande(client_as, user2, demande):
    res = client_as(user2).delete(f"/api/demandes/{demande.id}/")
    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_owner_can_edit_own_demande(client_as, user, demande):
    res = client_as(user).patch(f"/api/demandes/{demande.id}/", {"places": 2})
    assert res.status_code == status.HTTP_200_OK


# ── Conversation membership: messages ───────────────────────────────────
def _messages_url(corr_id):
    return f"/api/correspondances/{corr_id}/messages/"


@pytest.mark.django_db
def test_non_participant_cannot_post_message(client_as, user2, completed_voyage):
    corr = Correspondance.objects.get(voyage=completed_voyage)
    res = client_as(user2).post(_messages_url(corr.id), {"content": "intrusion"})
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_participant_cannot_post_before_validation(client_as, user, correspondance):
    # `correspondance` fixture is NOT validated.
    res = client_as(user).post(_messages_url(correspondance.id), {"content": "early"})
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_participant_can_post_when_validated(client_as, user, completed_voyage):
    corr = Correspondance.objects.get(voyage=completed_voyage)  # validated
    res = client_as(user).post(_messages_url(corr.id), {"content": "hello driver"})
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_non_participant_cannot_read_messages(client_as, user2, completed_voyage):
    corr = Correspondance.objects.get(voyage=completed_voyage)
    res = client_as(user2).get(_messages_url(corr.id))
    # Membership filter empties the queryset for outsiders.
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    results = body.get("results", body)
    assert results == [] or results == {"results": []}


# ── Reviews: participation required ─────────────────────────────────────
@pytest.mark.django_db
def test_outsider_cannot_review(client_as, user2, driver, completed_voyage):
    res = client_as(user2).post(
        "/api/avis/",
        {"voyage": completed_voyage.id, "utilisateur_note": driver.id, "note": 1},
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert not Avis.objects.filter(auteur=user2).exists()


@pytest.mark.django_db
def test_participant_can_review(client_as, user, driver, completed_voyage):
    res = client_as(user).post(
        "/api/avis/",
        {"voyage": completed_voyage.id, "utilisateur_note": driver.id, "note": 5,
         "commentaire": "Super conducteur"},
    )
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_duplicate_review_rejected(client_as, user, driver, completed_voyage):
    payload = {"voyage": completed_voyage.id, "utilisateur_note": driver.id, "note": 5}
    assert client_as(user).post("/api/avis/", payload).status_code == status.HTTP_201_CREATED
    assert client_as(user).post("/api/avis/", payload).status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_can_review_helper_matrix(user, user2, driver, completed_voyage):
    ok, _ = can_review(user, completed_voyage, driver)
    assert ok is True
    bad, _ = can_review(user2, completed_voyage, driver)
    assert bad is False
    self_review, _ = can_review(driver, completed_voyage, driver)
    assert self_review is False


# ── Enumeration & PII ───────────────────────────────────────────────────
@pytest.mark.django_db
def test_users_list_requires_auth():
    res = APIClient().get("/api/users/")
    assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_user_serializer_has_no_email(client_as, user):
    res = client_as(user).get("/api/users/")
    body = res.json()
    results = body.get("results", body)
    assert results, "expected at least one user"
    assert "email" not in results[0]


@pytest.mark.django_db
def test_public_profile_hides_contact_pii(client_as, user):
    res = client_as(user).get(f"/api/profiles/{user.profile.id}/")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "email" not in data
    assert "phone" not in data


@pytest.mark.django_db
def test_voyage_listing_does_not_leak_driver_phone(api_client, voyage):
    res = api_client.get("/api/voyages/")
    body = res.json()
    results = body.get("results", body)
    assert results, "expected at least one voyage"
    assert "phone" not in results[0]["conducteur_profile"]


@pytest.mark.django_db
def test_matched_users_get_contact_phone(client_as, user, driver, completed_voyage):
    # Give the driver a phone so the matched passenger can retrieve it.
    profile = driver.profile
    profile.phone = "+237650000000"
    profile.save()
    corr = Correspondance.objects.get(voyage=completed_voyage)
    res = client_as(user).get(f"/api/correspondances/{corr.id}/")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["contact_phone"] == "+237650000000"
