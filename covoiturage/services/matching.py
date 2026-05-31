"""Channel-agnostic match engine.

Single source of truth for scoring a Voyage against a Demande, replacing the two
divergent scorers that previously lived in ``signals.py`` and ``api/views.py``.

Matching works in two stages:
  1. A cheap DB prefilter (date window + optional bounding box).
  2. A corridor test in Python when both sides have coordinates, otherwise a
     graceful fallback to exact city-name matching (used by USSD/no-GPS users).
"""

from datetime import timedelta

from django.conf import settings
from django.db.models import Q

from covoiturage import geo
from covoiturage.models import Voyage, Demande, Correspondance


def _coords(obj, prefix):
    """Return ``(lat, lon)`` for a model's start/end point, or ``None``."""
    lat = getattr(obj, f"{prefix}_latitude", None)
    lon = getattr(obj, f"{prefix}_longitude", None)
    if lat is None or lon is None:
        return None
    return (lat, lon)


def _date_window(center_date):
    return center_date - timedelta(days=1), center_date + timedelta(days=1)


def _date_score(voyage, demande):
    day_diff = abs((voyage.date_depart.date() - demande.date_voyage).days)
    if day_diff == 0:
        return 1.0
    if day_diff == 1:
        return 0.6
    return 0.0


def compute_match_score(voyage, demande):
    """Return a match score in [0.0, 1.0]; 0.0 means "not a match".

    Blends date proximity with route geometry. When coordinates are available on
    both sides it scores by detour distance and direction; otherwise it falls
    back to exact (case-insensitive) city matching.
    """
    if voyage.places_disponibles < demande.places:
        return 0.0

    # Women-only rides never match non-female passengers.
    if getattr(voyage, "women_only", False):
        passenger_profile = getattr(demande.passager, "profile", None)
        if not (passenger_profile and passenger_profile.is_female):
            return 0.0

    date_score = _date_score(voyage, demande)
    if date_score <= 0:
        return 0.0

    v_start = _coords(voyage, "start")
    v_end = _coords(voyage, "end")
    d_start = _coords(demande, "start")
    d_end = _coords(demande, "end")

    use_corridor = (
        getattr(settings, "CORRIDOR_MATCHING_ENABLED", True)
        and all([v_start, v_end, d_start, d_end])
    )

    if use_corridor:
        pickup_detour = geo.point_to_segment_km(d_start, v_start, v_end)
        dropoff_detour = geo.point_to_segment_km(d_end, v_start, v_end)
        max_pickup = getattr(settings, "MAX_PICKUP_DETOUR_KM", 5)
        max_dropoff = getattr(settings, "MAX_DROPOFF_DETOUR_KM", 5)
        if pickup_detour > max_pickup or dropoff_detour > max_dropoff:
            return 0.0

        # Dropoff must be downstream of pickup (no backtracking).
        pickup_t = geo.progress_along_segment(d_start, v_start, v_end)
        dropoff_t = geo.progress_along_segment(d_end, v_start, v_end)
        if dropoff_t < pickup_t:
            return 0.0

        # Closer to the route = higher geo score.
        geo_score = 1.0 - (pickup_detour + dropoff_detour) / (max_pickup + max_dropoff)
        geo_score = max(0.0, min(1.0, geo_score))
        score = 0.5 * date_score + 0.5 * geo_score
    else:
        # City-name fallback (USSD / no coordinates).
        same_route = (
            voyage.ville_depart.strip().lower() == demande.ville_depart.strip().lower()
            and voyage.ville_arrivee.strip().lower()
            == demande.ville_arrivee.strip().lower()
        )
        if not same_route:
            return 0.0
        score = date_score

    return round(min(score, 1.0), 2)


def try_create_match(voyage, demande):
    """Create a Correspondance if voyage/demande are compatible. Returns it or None."""
    from covoiturage.notifications import notify_new_match

    if voyage.conducteur_id == demande.passager_id:
        return None
    score = compute_match_score(voyage, demande)
    if score <= 0:
        return None
    correspondance, created = Correspondance.objects.get_or_create(
        voyage=voyage, demande=demande, defaults={"score_match": score}
    )
    if created:
        notify_new_match(correspondance)
    return correspondance


def find_matches_for_voyage(voyage):
    """Find compatible demandes for a newly published voyage and create matches."""
    if voyage.est_termine:
        return []
    date_min, date_max = _date_window(voyage.date_depart.date())
    candidates = Demande.objects.filter(date_voyage__range=(date_min, date_max))
    if not getattr(settings, "CORRIDOR_MATCHING_ENABLED", True):
        candidates = candidates.filter(
            ville_depart__iexact=voyage.ville_depart,
            ville_arrivee__iexact=voyage.ville_arrivee,
        )
    created = []
    for demande in candidates:
        match = try_create_match(voyage, demande)
        if match:
            created.append(match)
    return created


def find_matches_for_demande(demande):
    """Find compatible voyages for a newly published demande and create matches."""
    date_min, date_max = _date_window(demande.date_voyage)
    candidates = Voyage.objects.filter(
        date_depart__date__range=(date_min, date_max), est_termine=False
    )
    if not getattr(settings, "CORRIDOR_MATCHING_ENABLED", True):
        candidates = candidates.filter(
            ville_depart__iexact=demande.ville_depart,
            ville_arrivee__iexact=demande.ville_arrivee,
        )
    created = []
    for voyage in candidates:
        match = try_create_match(voyage, demande)
        if match:
            created.append(match)
    return created
