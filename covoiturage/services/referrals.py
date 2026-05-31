"""Referral program: invite codes credit both users on the referee's first
completed trip. Reuses Wallet/Transaction (atomic, F()) — the escrow pattern.
"""

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F

from covoiturage.models import Profile, Wallet, Transaction


class ReferralError(Exception):
    pass


def apply_referral(new_user, code):
    """Attach ``new_user`` to the owner of ``code``. Idempotent-ish: refuses if the
    user already has a referrer or the code is invalid/self-referring."""
    code = (code or "").strip().upper()
    if not code:
        return None
    profile = new_user.profile
    if profile.referred_by_id:
        raise ReferralError("Un parrain est déjà enregistré.")
    referrer_profile = Profile.objects.filter(referral_code=code).select_related("user").first()
    if referrer_profile is None:
        raise ReferralError("Code de parrainage invalide.")
    if referrer_profile.user_id == new_user.id:
        raise ReferralError("Vous ne pouvez pas utiliser votre propre code.")
    profile.referred_by = referrer_profile.user
    profile.save(update_fields=["referred_by"])
    return referrer_profile.user


def _bonus():
    return Decimal(str(getattr(settings, "REFERRAL_BONUS_XAF", 500))).quantize(Decimal("0.01"))


def grant_referral_bonus(user):
    """Credit referrer + referee once, on the referee's first completed trip.

    Returns the bonus amount granted, or Decimal('0.00') if nothing happened.
    Guard: a referee receives at most one 'referral' transaction ever.
    """
    profile = getattr(user, "profile", None)
    if profile is None or not profile.referred_by_id:
        return Decimal("0.00")

    referee_wallet, _ = Wallet.objects.get_or_create(user=user)
    if Transaction.objects.filter(
        wallet=referee_wallet, transaction_type="referral"
    ).exists():
        return Decimal("0.00")  # already granted

    bonus = _bonus()
    referrer_wallet, _ = Wallet.objects.get_or_create(user=profile.referred_by)

    with transaction.atomic():
        for wallet, who in ((referee_wallet, "filleul"), (referrer_wallet, "parrain")):
            Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + bonus)
            Transaction.objects.create(
                wallet=wallet,
                amount=bonus,
                transaction_type="referral",
                description=f"Bonus de parrainage ({who})",
            )
    return bonus
