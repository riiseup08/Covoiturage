from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_driver = models.BooleanField(default=False)

    def __str__(self):
        return f"Profil de {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Voyage(models.Model):
    conducteur = models.ForeignKey(User, on_delete=models.CASCADE)
    ville_depart = models.CharField(max_length=100)
    lieu_ramassage = models.CharField(max_length=200, blank=True, null=True, help_text="Lieu exact du rendez-vous")
    ville_arrivee = models.CharField(max_length=100)
    date_depart = models.DateTimeField()
    date_arrivee = models.DateTimeField()
    places_disponibles = models.PositiveIntegerField(default=1)
    prix_par_place = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Véhicule et bagages
    plaque_immatriculation = models.CharField(
        max_length=20, help_text="Plaque d'immatriculation du véhicule",
        default=''
    )
    modele_voiture = models.CharField(
        max_length=100, help_text="Marque et modèle du véhicule (ex: Toyota Corolla)",
        default=''
    )
    BAGAGE_CHOICES = [
        ('petit', 'Petit (sac à main, petit sac)'),
        ('moyen', 'Moyen (valise cabine)'),
        ('gros', 'Gros (valises, encombrants)'),
        ('tous', 'Tous types acceptés'),
    ]
    type_bagage_accepte = models.CharField(
        max_length=10, choices=BAGAGE_CHOICES, default='moyen',
        help_text="Type de bagage accepté dans le véhicule"
    )
    est_termine = models.BooleanField(
        default=False,
        help_text="Coché quand le trajet est terminé (masqué des recherches)"
    )

    def __str__(self):
        return f"Trajet de {self.conducteur.username}: {self.ville_depart} -> {self.ville_arrivee}"

class Demande(models.Model):
    passager = models.ForeignKey(User, on_delete=models.CASCADE)
    ville_depart = models.CharField(max_length=100)
    ville_arrivee = models.CharField(max_length=100)
    date_voyage = models.DateField()
    places = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Demande de {self.passager.username}: {self.ville_depart} -> {self.ville_arrivee}"

class Correspondance(models.Model):
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE)
    demande = models.ForeignKey(Demande, on_delete=models.CASCADE)
    score_match = models.FloatField()
    is_validated = models.BooleanField(default=False)
    refus_conducteur = models.BooleanField(default=False, help_text="Le conducteur a refusé ce match")
    refus_passager = models.BooleanField(default=False, help_text="Le passager a annulé son intérêt")

    def __str__(self):
        return f"Match: {self.voyage} <-> {self.demande}"


class Avis(models.Model):
    """Avis laissé après un trajet terminé (conducteur sur passager ou passager sur conducteur)."""
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_donnes')
    utilisateur_note = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_recus')
    note = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], help_text="Note de 1 à 5")
    commentaire = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['voyage', 'auteur', 'utilisateur_note']]
        verbose_name_plural = 'Avis'

    def __str__(self):
        return f"{self.auteur.username} → {self.utilisateur_note.username} ({self.note}/5)"
