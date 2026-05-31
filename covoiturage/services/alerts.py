"""Saved-route alerts: notify subscribers when a matching trip is published."""

from covoiturage.models import RouteAlert
from covoiturage.notifications import create_notification


def notify_route_alerts(voyage):
    """Notify users whose active RouteAlert matches this newly-published trip.

    Sends in-app + SMS (via create_notification) so feature-phone users are reached.
    Skips the driver and respects women-only visibility.
    """
    alerts = RouteAlert.objects.filter(
        active=True,
        ville_depart__iexact=voyage.ville_depart.strip(),
        ville_arrivee__iexact=voyage.ville_arrivee.strip(),
    ).exclude(user_id=voyage.conducteur_id).select_related("user", "user__profile")

    notified = 0
    for alert in alerts:
        # Women-only trips alert only female subscribers.
        if voyage.women_only and not getattr(
            getattr(alert.user, "profile", None), "is_female", False
        ):
            continue
        create_notification(
            user=alert.user,
            notification_type="match",
            title="Nouveau trajet sur votre route",
            message=(
                f"Un trajet {voyage.ville_depart} → {voyage.ville_arrivee} "
                f"est disponible le {voyage.date_depart.strftime('%d/%m à %H:%M')}."
            ),
            related_voyage=voyage,
            send_email=False,
        )
        notified += 1
    return notified
