"""Tests for the referral program."""

from decimal import Decimal

import pytest
from django.test import override_settings

from covoiturage.models import Wallet, Transaction
from covoiturage.services import referrals, trips


@pytest.mark.django_db
def test_referral_code_generated_and_unique(user, user2):
    assert user.profile.referral_code
    assert user2.profile.referral_code
    assert user.profile.referral_code != user2.profile.referral_code


@pytest.mark.django_db
def test_apply_referral_links_users(user, user2):
    referrals.apply_referral(user2, user.profile.referral_code)
    user2.profile.refresh_from_db()
    assert user2.profile.referred_by_id == user.id


@pytest.mark.django_db
def test_cannot_self_refer(user):
    with pytest.raises(referrals.ReferralError):
        referrals.apply_referral(user, user.profile.referral_code)


@pytest.mark.django_db
def test_invalid_code_rejected(user2):
    with pytest.raises(referrals.ReferralError):
        referrals.apply_referral(user2, "NOPE999")


@override_settings(REFERRAL_BONUS_XAF=500)
@pytest.mark.django_db
def test_bonus_credits_both_on_first_completed_trip(driver, user, completed_voyage):
    # `user` (passenger on completed_voyage) was referred by `driver`.
    referrals.apply_referral(user, driver.profile.referral_code)
    completed_voyage.est_termine = False
    completed_voyage.save()

    trips.complete_voyage(driver, completed_voyage)

    referee_wallet = Wallet.objects.get(user=user)
    referrer_wallet = Wallet.objects.get(user=driver)
    assert Transaction.objects.filter(wallet=referee_wallet, transaction_type="referral").count() == 1
    assert Transaction.objects.filter(wallet=referrer_wallet, transaction_type="referral").count() == 1
    # referee balance includes the +500 bonus
    assert referee_wallet.balance == Decimal("500.00")


@override_settings(REFERRAL_BONUS_XAF=500)
@pytest.mark.django_db
def test_bonus_granted_only_once(driver, user, completed_voyage):
    referrals.apply_referral(user, driver.profile.referral_code)
    referrals.grant_referral_bonus(user)
    first = Wallet.objects.get(user=user).balance
    referrals.grant_referral_bonus(user)  # second call must be a no-op
    assert Wallet.objects.get(user=user).balance == first


@pytest.mark.django_db
def test_no_bonus_without_referrer(user):
    assert referrals.grant_referral_bonus(user) == Decimal("0.00")
