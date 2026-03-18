from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg
from .models import Profile, Voyage, Demande, Correspondance, Avis


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Ensure a Profile is created when a User is created."""
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure Profile exists and has created_at set to avoid NOT NULL errors."""
    profile, _ = Profile.objects.get_or_create(user=instance)
    if profile.created_at is None:
        profile.created_at = timezone.now()
    profile.save()

def _compute_match_score(voyage, demande):
    """Compute a match score (0.0-1.0) between a Voyage and a Demande.

    Factors:
    - Date proximity: exact same day = 1.0, +/-1 day = 0.7
    - Place availability: enough places = +0 penalty, else skip
    - City name: exact = 1.0 (already filtered by iexact)
    """
    from datetime import timedelta
    day_diff = abs((voyage.date_depart.date() - demande.date_voyage).days)
    if day_diff == 0:
        date_score = 1.0
    elif day_diff == 1:
        date_score = 0.7
    else:
        return 0.0  # too far apart
    return round(date_score, 2)


def _try_create_match(voyage, demande):
    """Attempt to create a Correspondance between a voyage and demande."""
    from .notifications import notify_new_match
    if voyage.conducteur_id == demande.passager_id:
        return
    if voyage.places_disponibles < demande.places:
        return
    score = _compute_match_score(voyage, demande)
    if score <= 0:
        return
    correspondance, created = Correspondance.objects.get_or_create(
        voyage=voyage, demande=demande,
        defaults={'score_match': score}
    )
    if created:
        notify_new_match(correspondance)


@receiver(post_save, sender=Voyage)
def create_voyage_matches(sender, instance, created, **kwargs):
    """Quand un conducteur publie un voyage, on cherche les passagers compatibles."""
    if created:
        from datetime import timedelta
        date_min = instance.date_depart.date() - timedelta(days=1)
        date_max = instance.date_depart.date() + timedelta(days=1)
        demandes_compatibles = Demande.objects.filter(
            ville_depart__iexact=instance.ville_depart,
            ville_arrivee__iexact=instance.ville_arrivee,
            date_voyage__range=(date_min, date_max),
        )
        for demande in demandes_compatibles:
            _try_create_match(instance, demande)


@receiver(post_save, sender=Demande)
def create_demande_matches(sender, instance, created, **kwargs):
    """Quand un passager publie une demande, on cherche les voyages compatibles."""
    if created:
        from datetime import timedelta
        date_min = instance.date_voyage - timedelta(days=1)
        date_max = instance.date_voyage + timedelta(days=1)
        voyages_compatibles = Voyage.objects.filter(
            ville_depart__iexact=instance.ville_depart,
            ville_arrivee__iexact=instance.ville_arrivee,
            date_depart__date__range=(date_min, date_max),
            est_termine=False,
        )
        for voyage in voyages_compatibles:
            _try_create_match(voyage, instance)


@receiver(post_save, sender=Avis)
def update_trust_score_on_review(sender, instance, **kwargs):
    """Recalculate trust_score for the reviewed user based on average rating.

    Formula: base 50 + (avg_note - 3) * 10, clamped to 0-100.
    A user with no reviews keeps the default 50.
    """
    user = instance.utilisateur_note
    avg = Avis.objects.filter(utilisateur_note=user).aggregate(avg=Avg('note'))['avg']
    if avg is not None:
        score = int(50 + (avg - 3) * 10)
        score = max(0, min(100, score))
        Profile.objects.filter(user=user).update(trust_score=score)
