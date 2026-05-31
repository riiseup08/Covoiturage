"""Tests for Mobile-Money escrow flow (services/escrow.py) using the stub provider."""

from decimal import Decimal

import pytest

from covoiturage.models import Wallet, Transaction
from covoiturage.payments.stub import StubProvider
from covoiturage.services import escrow, trips


@pytest.fixture(autouse=True)
def _reset_stub():
    StubProvider.reset()
    yield
    StubProvider.reset()


@pytest.mark.django_db
def test_hold_requires_validation(correspondance):
    with pytest.raises(escrow.EscrowError):
        escrow.hold(correspondance, phone="650000000")


@pytest.mark.django_db
def test_full_hold_release_pays_driver_minus_commission(correspondance):
    correspondance.is_validated = True
    correspondance.save()

    escrow.hold(correspondance, phone="650000000")
    correspondance.refresh_from_db()
    assert correspondance.payment_status == "held"
    # voyage.prix_par_place=5000, places=1 -> fare 5000
    assert correspondance.escrow_amount == Decimal("5000.00")

    voyage = correspondance.voyage
    voyage.driver_confirmed_pickup = True
    voyage.driver_confirmed_dropoff = True
    voyage.save()

    escrow.release(correspondance)
    correspondance.refresh_from_db()
    assert correspondance.payment_status == "released"

    wallet = Wallet.objects.get(user=voyage.conducteur)
    # driver gets 5000 - 10% commission = 4500
    assert wallet.balance == Decimal("4500.00")
    assert Transaction.objects.filter(wallet=wallet, transaction_type="commission").exists()
    assert Transaction.objects.filter(wallet=wallet, transaction_type="topup").exists()


@pytest.mark.django_db
def test_release_blocked_without_both_confirmations(correspondance):
    correspondance.is_validated = True
    correspondance.save()
    escrow.hold(correspondance, phone="650000000")

    voyage = correspondance.voyage
    voyage.driver_confirmed_pickup = True  # only one
    voyage.save()

    with pytest.raises(escrow.EscrowError):
        escrow.release(correspondance)


@pytest.mark.django_db
def test_refund_before_pickup(correspondance):
    correspondance.is_validated = True
    correspondance.save()
    escrow.hold(correspondance, phone="650000000")

    escrow.refund(correspondance)
    correspondance.refresh_from_db()
    assert correspondance.payment_status == "refunded"


@pytest.mark.django_db
def test_complete_voyage_uses_decimal_no_crash(driver, completed_voyage):
    """Regression: completing a priced trip with a validated passenger must not raise
    a Decimal*float TypeError and must debit the correct commission."""
    completed_voyage.est_termine = False
    completed_voyage.save()

    commission = trips.complete_voyage(driver, completed_voyage)
    # prix 3500 * 1 passenger * 10% = 350.00
    assert commission == Decimal("350.00")
    wallet = Wallet.objects.get(user=driver)
    assert wallet.balance == Decimal("-350.00")
