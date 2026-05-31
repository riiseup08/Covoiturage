"""Signal handlers — thin wrappers over the service layer.

User profile/wallet creation lives in ``models.py``; this module only wires the
domain events (new trip/request -> matching, new review -> trust score).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg

from .models import Voyage, Demande, Avis, Profile
from .services import matching


@receiver(post_save, sender=Voyage, dispatch_uid="voyage_matches")
def create_voyage_matches(sender, instance, created, **kwargs):
    """When a driver publishes a trip, find compatible passengers and fire
    saved-route alerts for subscribers watching this corridor."""
    if created:
        matching.find_matches_for_voyage(instance)
        from .services.alerts import notify_route_alerts
        notify_route_alerts(instance)


@receiver(post_save, sender=Demande, dispatch_uid="demande_matches")
def create_demande_matches(sender, instance, created, **kwargs):
    """When a passenger publishes a request, find compatible trips."""
    if created:
        matching.find_matches_for_demande(instance)


@receiver(post_save, sender=Avis, dispatch_uid="trust_score")
def update_trust_score_on_review(sender, instance, **kwargs):
    """Recalculate trust_score: base 50 + (avg_note - 3) * 10, clamped 0-100."""
    user = instance.utilisateur_note
    avg = Avis.objects.filter(utilisateur_note=user).aggregate(avg=Avg("note"))["avg"]
    if avg is not None:
        score = max(0, min(100, int(50 + (avg - 3) * 10)))
        Profile.objects.filter(user=user).update(trust_score=score)
