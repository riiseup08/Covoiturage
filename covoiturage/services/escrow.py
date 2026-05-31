"""Mobile-Money escrow state machine.

Passenger fare is held on match validation and released to the driver only after
both pickup and dropoff are confirmed — converting the platform from lead-gen
into trusted payments. All wallet writes are atomic.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F

from covoiturage.models import Wallet, Transaction
from covoiturage.payments import get_provider
from covoiturage.services.trips import COMMISSION_RATE


class EscrowError(Exception):
    """Raised when an escrow transition is not allowed."""


def _fare_for(correspondance):
    voyage = correspondance.voyage
    places = correspondance.demande.places or 1
    # Coerce defensively: a DecimalField only yields Decimal after a DB round-trip;
    # an in-memory instance can still hold the float it was assigned.
    price = Decimal(str(voyage.prix_par_place))
    return (price * places).quantize(Decimal("0.01"))


def hold(correspondance, phone, provider="mtn"):
    """Charge the passenger and move funds into escrow. Requires a validated match."""
    if not correspondance.is_validated:
        raise EscrowError("Le match doit être validé avant le paiement.")
    if correspondance.payment_status != "none":
        raise EscrowError("Un paiement existe déjà pour ce match.")

    amount = _fare_for(correspondance)
    result = get_provider().request_payment(
        phone=phone, amount=amount, provider=provider,
        reference=f"escrow-{correspondance.id}",
    )
    if not result.success:
        raise EscrowError(result.error or "Échec du paiement Mobile Money.")

    correspondance.escrow_amount = amount
    correspondance.escrow_reference = result.reference
    correspondance.payment_status = "held"
    correspondance.save(update_fields=["escrow_amount", "escrow_reference", "payment_status"])
    return correspondance


def release(correspondance, driver_phone=None):
    """Release escrow to the driver minus commission. Requires both confirmations."""
    if correspondance.payment_status != "held":
        raise EscrowError("Aucun fonds en attente de libération.")
    voyage = correspondance.voyage
    if not (voyage.driver_confirmed_pickup and voyage.driver_confirmed_dropoff):
        raise EscrowError("La prise en charge et la dépose doivent être confirmées.")

    amount = correspondance.escrow_amount
    commission = (amount * COMMISSION_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    driver_share = amount - commission
    driver = voyage.conducteur
    phone = driver_phone or getattr(getattr(driver, "profile", None), "phone", "") or ""

    payout = get_provider().payout(
        phone=phone, amount=driver_share, provider="mtn",
        reference=correspondance.escrow_reference,
    )
    if not payout.success:
        raise EscrowError(payout.error or "Échec du versement au conducteur.")

    with transaction.atomic():
        wallet, _ = Wallet.objects.get_or_create(user=driver)
        Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + driver_share)
        Transaction.objects.create(
            wallet=wallet, amount=driver_share, transaction_type="topup",
            description=f"Versement course {voyage.ville_depart} -> {voyage.ville_arrivee}",
            related_voyage=voyage, external_reference=correspondance.escrow_reference,
        )
        Transaction.objects.create(
            wallet=wallet, amount=-commission, transaction_type="commission",
            description=f"Commission course {voyage.ville_depart} -> {voyage.ville_arrivee}",
            related_voyage=voyage,
        )
        correspondance.payment_status = "released"
        correspondance.save(update_fields=["payment_status"])
    return correspondance


def refund(correspondance):
    """Refund held funds to the passenger (cancellation before pickup)."""
    if correspondance.payment_status != "held":
        raise EscrowError("Aucun fonds à rembourser.")
    if correspondance.voyage.driver_confirmed_pickup:
        raise EscrowError("Impossible de rembourser après la prise en charge.")

    result = get_provider().refund(
        reference=correspondance.escrow_reference, amount=correspondance.escrow_amount
    )
    if not result.success:
        raise EscrowError(result.error or "Échec du remboursement.")

    correspondance.payment_status = "refunded"
    correspondance.save(update_fields=["payment_status"])
    return correspondance
