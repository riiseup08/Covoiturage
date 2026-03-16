from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from PIL import Image
import os

class Profile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('not_started', 'Not Verified'),
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
    phone_verified = models.BooleanField(default=False)
    is_driver = models.BooleanField(default=False)
    
    # Profile & Safety Photos
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    car_photo = models.ImageField(
        upload_to='car_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Photo of your vehicle for verification"
    )
    
    # ID Verification
    id_type = models.CharField(
        max_length=50, 
        choices=[
            ('national_id', 'National ID'),
            ('passport', 'Passport'),
            ('drivers_license', 'Driver\'s License'),
            ('other', 'Other'),
        ],
        blank=True
    )
    id_number = models.CharField(max_length=50, blank=True)
    id_photo = models.ImageField(
        upload_to='id_photos/',
        blank=True,
        null=True,
        help_text="Photo of your ID for verification"
    )
    id_verified = models.BooleanField(default=False)
    
    # Driver License Information
    driver_license_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    driver_license_photo = models.ImageField(
        upload_to='driver_license_photos/',
        blank=True,
        null=True,
        help_text="Photo of your driver's license"
    )
    driver_license_verified = models.BooleanField(default=False)
    driver_license_expiry = models.DateField(blank=True, null=True)
    
    # Verification Status
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='not_started'
    )
    verification_notes = models.TextField(blank=True, help_text="Admin notes on verification")
    
    # Trust Score (0-100)
    trust_score = models.IntegerField(default=50, help_text="0-100 score based on verification and ratings")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Resize and optimize uploaded images"""
        if self.profile_photo:
            self._resize_image(self.profile_photo, (300, 300))
        if self.car_photo:
            self._resize_image(self.car_photo, (600, 400))
        if self.id_photo:
            self._resize_image(self.id_photo, (400, 300))
        if self.driver_license_photo:
            self._resize_image(self.driver_license_photo, (400, 250))
        super().save(*args, **kwargs)
    
    def _resize_image(self, image_field, max_size):
        """Resize image to max dimensions while maintaining aspect ratio"""
        if image_field and image_field.name:
            try:
                img = Image.open(image_field.open('rb'))
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(image_field.path, quality=85, optimize=True)
            except Exception:
                pass  # If resizing fails, continue anyway


class PhoneOTP(models.Model):
    """SMS OTP for phone verification"""
    phone = models.CharField(max_length=20)
    otp_code = models.CharField(max_length=6)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Phone OTP"
        verbose_name_plural = "Phone OTPs"
    
    def __str__(self):
        return f"OTP for {self.phone}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Voyage(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
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
    
    # Status & Validation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='upcoming'
    )
    is_validated = models.BooleanField(
        default=False,
        help_text="Both driver and passenger have confirmed pickup/dropoff"
    )
    
    # GPS Tracking
    start_latitude = models.FloatField(null=True, blank=True, help_text="Latitude at trip start")
    start_longitude = models.FloatField(null=True, blank=True, help_text="Longitude at trip start")
    end_latitude = models.FloatField(null=True, blank=True, help_text="Latitude at trip end")
    end_longitude = models.FloatField(null=True, blank=True, help_text="Longitude at trip end")
    
    # Safety
    driver_confirmed_pickup = models.BooleanField(default=False)
    driver_confirmed_dropoff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class TripValidation(models.Model):
    """Track pickup and dropoff confirmations for safety"""
    voyage = models.OneToOneField(Voyage, on_delete=models.CASCADE, related_name='validation')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Pickup confirmation
    pickup_confirmed_by_driver = models.BooleanField(default=False)
    pickup_confirmed_by_passenger = models.BooleanField(default=False)
    pickup_confirmed_at = models.DateTimeField(null=True, blank=True)
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    
    # Dropoff confirmation
    dropoff_confirmed_by_driver = models.BooleanField(default=False)
    dropoff_confirmed_by_passenger = models.BooleanField(default=False)
    dropoff_confirmed_at = models.DateTimeField(null=True, blank=True)
    dropoff_latitude = models.FloatField(null=True, blank=True)
    dropoff_longitude = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Validation for {self.voyage}"
