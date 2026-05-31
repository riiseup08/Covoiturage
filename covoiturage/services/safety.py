"""Live-trip-share and SOS — let a rider share their trip with, or alert, their
emergency contact over SMS. Reuses the SMS gateway and a signed public link.
"""

from django.conf import settings
from django.core import signing

from covoiturage.messaging_gateway import get_gateway

_SALT = "covoiturage.trip-status"


class SafetyError(Exception):
    """Raised when a safety action can't proceed (not a participant, no contact)."""


def make_trip_token(correspondance):
    """Signed, URL-safe token identifying a correspondance for the public page."""
    return signing.dumps({"c": correspondance.id}, salt=_SALT)


def read_trip_token(token, max_age=None):
    """Return the correspondance id from a token, or None if invalid/expired."""
    try:
        data = signing.loads(token, salt=_SALT, max_age=max_age)
    except signing.BadSignature:
        return None
    return data.get("c")


def trip_status_url(correspondance):
    return f"{settings.SITE_URL}/trip-status/{make_trip_token(correspondance)}/"


def _require_participant(correspondance, user):
    if user.id not in (
        correspondance.voyage.conducteur_id,
        correspondance.demande.passager_id,
    ):
        raise SafetyError("Vous ne participez pas à ce trajet.")


def _emergency_phone(user):
    phone = (
        getattr(getattr(user, "profile", None), "emergency_contact_phone", "") or ""
    ).strip()
    if not phone:
        raise SafetyError("Aucun contact d'urgence enregistré dans votre profil.")
    return phone


def _trip_summary(correspondance):
    v = correspondance.voyage
    driver = v.conducteur
    return (
        f"{driver.get_full_name() or driver.username} "
        f"({v.modele_voiture or 'véhicule'} {v.plaque_immatriculation}) — "
        f"{v.ville_depart} → {v.ville_arrivee} le {v.date_depart.strftime('%d/%m %H:%M')}"
    )


def share_trip(correspondance, user):
    """SMS the user's emergency contact a link to follow this trip."""
    _require_participant(correspondance, user)
    phone = _emergency_phone(user)
    text = (
        f"{user.get_full_name() or user.username} partage son trajet Covoit.Africa: "
        f"{_trip_summary(correspondance)}. Suivi: {trip_status_url(correspondance)}"
    )[:320]
    get_gateway().send_sms(phone, text)
    return phone


def sos(correspondance, user):
    """Send an urgent SOS to the user's emergency contact with the trip details."""
    _require_participant(correspondance, user)
    phone = _emergency_phone(user)
    text = (
        f"🆘 URGENCE — {user.get_full_name() or user.username} a déclenché une alerte "
        f"pendant un trajet Covoit.Africa: {_trip_summary(correspondance)}. "
        f"Suivi: {trip_status_url(correspondance)}"
    )[:320]
    get_gateway().send_sms(phone, text)
    return phone
