"""Tests for the mobile-friendly auth endpoints (login/register/logout)."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_login_returns_token_and_profile(user):
    user.set_password("secret123")
    user.save()
    res = APIClient().post(
        "/api/auth/login/", {"username": "testuser", "password": "secret123"}
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["token"] and data["refresh"]
    assert data["username"] == "testuser"
    assert data["user_id"] == user.id
    assert "profile" in data and "referral_code" in data["profile"]


@pytest.mark.django_db
def test_login_rejects_bad_credentials(user):
    res = APIClient().post(
        "/api/auth/login/", {"username": "testuser", "password": "wrong"}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_returned_token_authenticates_subsequent_requests(user):
    user.set_password("secret123")
    user.save()
    token = APIClient().post(
        "/api/auth/login/", {"username": "testuser", "password": "secret123"}
    ).json()["token"]

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    res = client.get("/api/profiles/me/")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["username"] == "testuser"


@pytest.mark.django_db
def test_register_creates_user_and_returns_token():
    res = APIClient().post(
        "/api/auth/register/",
        {"username": "newbie", "email": "n@e.com", "password": "secret123"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["username"] == "newbie"
    assert data["token"]


@pytest.mark.django_db
def test_register_with_referral_links_referrer(user):
    code = user.profile.referral_code
    res = APIClient().post(
        "/api/auth/register/",
        {"username": "friend", "password": "secret123", "referral_code": code},
    )
    assert res.status_code == status.HTTP_201_CREATED
    from django.contrib.auth.models import User
    friend = User.objects.get(username="friend")
    assert friend.profile.referred_by_id == user.id


@pytest.mark.django_db
def test_register_rejects_duplicate_username(user):
    res = APIClient().post(
        "/api/auth/register/", {"username": "testuser", "password": "secret123"}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_logout_requires_auth_and_returns_204(user):
    client = APIClient()
    client.force_authenticate(user=user)
    assert client.post("/api/auth/logout/").status_code == status.HTTP_204_NO_CONTENT
    assert APIClient().post("/api/auth/logout/").status_code in (401, 403)
