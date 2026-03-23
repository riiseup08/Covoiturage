import secrets

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    """User profile with verification fields (aligned to existing DB schema)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_driver = models.BooleanField(default=False)

    # Photos
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    car_photo = models.ImageField(upload_to='car_photos/', blank=True, null=True)

    # ID verification
    id_type = models.CharField(max_length=50, blank=True, default='')
    id_number = models.CharField(max_length=50, blank=True, default='')
    id_photo = models.ImageField(upload_to='id_photos/', blank=True, null=True)
    id_verified = models.BooleanField(default=False)

    # Driver license verification
    driver_license_number = models.CharField(max_length=50, blank=True, null=True)
    driver_license_photo = models.ImageField(upload_to='driver_license_photos/', blank=True, null=True)
    driver_license_verified = models.BooleanField(default=False)
    driver_license_expiry = models.DateField(blank=True, null=True)

    # Phone verification
    phone_verified = models.BooleanField(default=False)

    # WhatsApp & Mobile Money (essential for Africa)
    whatsapp_number = models.CharField(max_length=20, blank=True, default='', help_text="Numéro WhatsApp (si différent)")
    mobile_money_number = models.CharField(max_length=20, blank=True, default='', help_text="Numéro Mobile Money (MTN, Orange, etc.)")
    MOBILE_MONEY_PROVIDER_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('orange', 'Orange Money'),
        ('moov', 'Moov Money'),
        ('airtel', 'Airtel Money'),
        ('wave', 'Wave'),
        ('other', 'Autre'),
    ]
    mobile_money_provider = models.CharField(max_length=10, choices=MOBILE_MONEY_PROVIDER_CHOICES, blank=True, default='')
    preferred_language = models.CharField(max_length=5, default='fr', choices=[('fr', 'Français'), ('en', 'English')])

    # Women-safety & emergency contacts
    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('other', 'Autre'),
        ('prefer_not', 'Préfère ne pas dire'),
    ]
    gender = models.CharField(max_length=12, choices=GENDER_CHOICES, blank=True, default='')
    emergency_contact_name = models.CharField(max_length=100, blank=True, default='', help_text="Nom du contact d'urgence")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, default='', help_text="Téléphone du contact d'urgence")

    # Status & scoring
    verification_status = models.CharField(max_length=20, default='not_started')
    verification_notes = models.TextField(blank=True, default='')
    trust_score = models.IntegerField(default=50)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

# NOTE: profile signals are in signals.py (loaded via apps.py ready())
# Do NOT duplicate them here.

class Voyage(models.Model):
    conducteur = models.ForeignKey(User, on_delete=models.CASCADE)
    ville_depart = models.CharField(max_length=100)
    lieu_ramassage = models.CharField(max_length=200, blank=True, null=True, help_text="Lieu exact du rendez-vous")
    ville_arrivee = models.CharField(max_length=100)
    date_depart = models.DateTimeField()
    date_arrivee = models.DateTimeField()
    places_disponibles = models.PositiveIntegerField(default=1)
    prix_par_place = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    CURRENCY_CHOICES = [
        ('XAF', 'FCFA (Afrique Centrale)'),
        ('XOF', 'FCFA (Afrique de l\'Ouest)'),
        ('NGN', 'Naira (Nigeria)'),
        ('GHS', 'Cedi (Ghana)'),
        ('KES', 'Shilling (Kenya)'),
        ('ZAR', 'Rand (Afrique du Sud)'),
        ('MAD', 'Dirham (Maroc)'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='XAF')
    accept_mobile_money = models.BooleanField(default=True, help_text="Accepte le paiement par Mobile Money")
    accept_cash = models.BooleanField(default=True, help_text="Accepte le paiement en espèces")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Validation et statut du trajet
    is_validated = models.BooleanField(default=False, help_text="Trajet validé par l'équipe")
    status = models.CharField(max_length=20, default='pending', help_text="Statut global du trajet")
    driver_confirmed_pickup = models.BooleanField(default=False, help_text="Le conducteur confirme la prise en charge")
    driver_confirmed_dropoff = models.BooleanField(default=False, help_text="Le conducteur confirme la dépose")

    # Localisation (optionnelle)
    start_latitude = models.FloatField(blank=True, null=True)
    start_longitude = models.FloatField(blank=True, null=True)
    end_latitude = models.FloatField(blank=True, null=True)
    end_longitude = models.FloatField(blank=True, null=True)

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
    women_only = models.BooleanField(
        default=False,
        help_text="Trajet réservé aux femmes"
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


class Notification(models.Model):
    """In-app notifications for users."""
    TYPE_CHOICES = [
        ('match', 'Nouveau match trouvé'),
        ('match_validated', 'Match validé'),
        ('match_refused', 'Match refusé'),
        ('review', 'Nouvel avis reçu'),
        ('trip_reminder', 'Rappel de trajet'),
        ('trip_completed', 'Trajet terminé'),
        ('message', 'Nouveau message'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, null=True, blank=True)
    related_correspondance = models.ForeignKey(Correspondance, on_delete=models.CASCADE, null=True, blank=True)
    related_avis = models.ForeignKey(Avis, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type}: {self.title}"
    
    @property
    def icon(self):
        """Return emoji icon based on notification type."""
        icons = {
            'match': '🤝',
            'match_validated': '✅',
            'match_refused': '❌',
            'review': '⭐',
            'trip_reminder': '📅',
            'trip_completed': '🚗',
            'message': '💬',
        }
        return icons.get(self.notification_type, '📌')


class Message(models.Model):
    """Direct message between matched users on a specific correspondance."""
    correspondance = models.ForeignKey(Correspondance, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['correspondance', 'created_at']),
        ]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class PhoneOTP(models.Model):
    """OTP codes for phone-based authentication."""
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', '-created_at']),
        ]

    def __str__(self):
        return f"OTP pour {self.phone}"

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired and self.attempts < 5

    @classmethod
    def generate(cls, phone):
        """Create a new 6-digit OTP for the given phone number."""
        # Invalidate previous unused OTPs for this phone
        cls.objects.filter(phone=phone, is_used=False).update(is_used=True)
        code = f"{secrets.randbelow(900000) + 100000}"
        return cls.objects.create(phone=phone, code=code)

    @classmethod
    def verify(cls, phone, code):
        """Verify an OTP. Returns True if valid, False otherwise."""
        otp = cls.objects.filter(phone=phone, is_used=False).order_by('-created_at').first()
        if not otp or not otp.is_valid:
            return False
        otp.attempts += 1
        if otp.code == code:
            otp.is_used = True
            otp.save(update_fields=['is_used', 'attempts'])
            return True
        otp.save(update_fields=['attempts'])
        return False
