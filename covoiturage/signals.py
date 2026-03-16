from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Profile, Voyage, Demande, Correspondance


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

@receiver(post_save, sender=Voyage)
def create_voyage_matches(sender, instance, created, **kwargs):
    """Quand un conducteur publie un voyage, on cherche les passagers compatibles"""
    if created:
        demandes_compatibles = Demande.objects.filter(
            ville_depart=instance.ville_depart,
            ville_arrivee=instance.ville_arrivee
        )
        for demande in demandes_compatibles:
            if demande.date_voyage == instance.date_depart.date():
                if demande.passager_id != instance.conducteur_id and instance.places_disponibles >= demande.places:
                    Correspondance.objects.get_or_create(
                        voyage=instance, demande=demande,
                        defaults={'score_match': 1.0}
                    )

@receiver(post_save, sender=Demande)
def create_demande_matches(sender, instance, created, **kwargs):
    """Quand un passager publie une demande, on cherche les voyages compatibles"""
    if created:
        voyages_compatibles = Voyage.objects.filter(
            ville_depart=instance.ville_depart,
            ville_arrivee=instance.ville_arrivee
        )
        for voyage in voyages_compatibles:
            if voyage.date_depart.date() == instance.date_voyage:
                if voyage.conducteur_id != instance.passager_id and voyage.places_disponibles >= instance.places:
                    Correspondance.objects.get_or_create(
                        voyage=voyage, demande=instance,
                        defaults={'score_match': 1.0}
                    )
