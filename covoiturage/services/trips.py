"""Channel-agnostic trip operations shared by web, REST API, and USSD."""

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from covoiturage import geo
from covoiturage.models import Voyage, Demande, Correspondance, Wallet, Transaction

COMMISSION_RATE = Decimal("0.10")


def _geocode_into(obj, prefix, place):
    """Populate ``{prefix}_latitude/longitude`` on obj from a place string."""
    if getattr(obj, f"{prefix}_latitude", None) is not None:
        return
    coords = geo.geocode_cached(place)
    if coords:
        setattr(obj, f"{prefix}_latitude", coords[0])
        setattr(obj, f"{prefix}_longitude", coords[1])


def publish_voyage(user, **fields):
    """Create a Voyage, geocoding its endpoints when coordinates are absent."""
    voyage = Voyage(conducteur=user, **fields)
    _geocode_into(voyage, "start", voyage.lieu_ramassage or voyage.ville_depart)
    _geocode_into(voyage, "end", voyage.ville_arrivee)
    voyage.save()  # post_save signal triggers matching
    return voyage


def publish_demande(user, **fields):
    """Create a Demande, geocoding its endpoints when coordinates are absent."""
    demande = Demande(passager=user, **fields)
    _geocode_into(demande, "start", demande.ville_depart)
    _geocode_into(demande, "end", demande.ville_arrivee)
    demande.save()  # post_save signal triggers matching
    return demande


def complete_voyage(user, voyage):
    """Mark a voyage terminated and deduct the platform commission atomically.

    Returns the commission charged (``Decimal``), 0 when no validated passengers.
    Fixes the prior ``Decimal * float`` TypeError and the non-atomic wallet write.
    """
    if voyage.conducteur_id != user.id or voyage.est_termine:
        return Decimal("0.00")

    validated = Correspondance.objects.filter(
        voyage=voyage, is_validated=True, refus_conducteur=False, refus_passager=False
    ).select_related("demande__passager")
    passagers_count = validated.count()

    # Coerce defensively: a DecimalField only yields Decimal after a DB round-trip;
    # an in-memory instance can still hold the float it was assigned.
    price = Decimal(str(voyage.prix_par_place))
    commission = (
        (price * passagers_count * COMMISSION_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if passagers_count
        else Decimal("0.00")
    )

    with transaction.atomic():
        voyage.est_termine = True
        voyage.save(update_fields=["est_termine"])
        if commission > 0:
            wallet, _ = Wallet.objects.get_or_create(user=user)
            Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") - commission)
            Transaction.objects.create(
                wallet=wallet,
                amount=-commission,
                transaction_type="commission",
                description=(
                    f"Commission trajet {voyage.ville_depart} -> {voyage.ville_arrivee} "
                    f"({passagers_count} passagers)"
                ),
                related_voyage=voyage,
            )

    # A completed trip is the trigger for referral bonuses (driver + each passenger).
    from covoiturage.services.referrals import grant_referral_bonus

    grant_referral_bonus(user)
    for c in validated:
        grant_referral_bonus(c.demande.passager)

    return commission


def search_voyages(filters, user=None):
    """Return a queryset of upcoming, available, non-terminated voyages.

    ``filters`` is a mapping (request GET / query params). Unknown keys are ignored.
    ``user`` (optional) is the searcher: women-only trips are hidden from anyone
    who is not a female user.
    """
    qs = (
        Voyage.objects.filter(
            date_depart__gte=timezone.now(),
            places_disponibles__gte=1,
            est_termine=False,
        )
        .select_related("conducteur", "conducteur__profile")
        .order_by("date_depart")
    )

    # Hide women-only trips from non-female searchers (anonymous included).
    is_female = bool(getattr(getattr(user, "profile", None), "is_female", False))
    if not is_female:
        qs = qs.exclude(women_only=True)

    if (filters.get("women_only") or "").strip() in ("1", "true", "yes", "on"):
        qs = qs.filter(women_only=True)

    ville_depart = (filters.get("ville_depart") or "").strip()
    ville_arrivee = (filters.get("ville_arrivee") or "").strip()
    if ville_depart:
        qs = qs.filter(ville_depart__icontains=ville_depart)
    if ville_arrivee:
        qs = qs.filter(ville_arrivee__icontains=ville_arrivee)

    date_str = (filters.get("date") or "").strip()
    if date_str:
        from datetime import datetime

        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            qs = qs.filter(date_depart__date=d)
        except ValueError:
            pass

    type_bagage = (filters.get("type_bagage") or filters.get("type_baggage") or "").strip()
    if type_bagage and type_bagage in dict(Voyage.BAGAGE_CHOICES):
        qs = qs.filter(type_bagage_accepte=type_bagage)

    for key, lookup in (("prix_max", "prix_par_place__lte"), ("places_min", "places_disponibles__gte")):
        raw = filters.get(key)
        if raw:
            try:
                qs = qs.filter(**{lookup: int(raw)})
            except (ValueError, TypeError):
                pass

    return qs
