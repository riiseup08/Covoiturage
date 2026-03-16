from django.contrib import admin
from .models import Profile, Voyage, Demande, Correspondance, Avis, PhoneOTP, TripValidation

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'utilisateur_note', 'voyage', 'note', 'created_at')
    list_filter = ('note', 'created_at')
    search_fields = ('auteur__username', 'utilisateur_note__username', 'commentaire')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'phone_verified', 'is_driver', 'verification_status', 'trust_score', 'created_at')
    list_filter = ('phone_verified', 'is_driver', 'verification_status', 'id_verified', 'driver_license_verified')
    search_fields = ('user__username', 'phone', 'id_number', 'driver_license_number')
    readonly_fields = ('created_at', 'updated_at', 'trust_score')
    
    fieldsets = (
        ('User Info', {'fields': ('user', 'bio', 'phone', 'phone_verified')}),
        ('Photos', {'fields': ('profile_photo', 'car_photo')}),
        ('ID Verification', {'fields': ('id_type', 'id_number', 'id_photo', 'id_verified')}),
        ('Driver License', {'fields': ('driver_license_number', 'driver_license_photo', 'driver_license_verified', 'driver_license_expiry')}),
        ('Verification Status', {'fields': ('verification_status', 'verification_notes', 'trust_score')}),
        ('Account Details', {'fields': ('is_driver', 'created_at', 'updated_at')}),
    )

@admin.register(Voyage)
class VoyageAdmin(admin.ModelAdmin):
    list_display = ('conducteur', 'ville_depart', 'ville_arrivee', 'date_depart', 'status', 'is_validated', 'places_disponibles')
    list_filter = ('status', 'est_termine', 'is_validated', 'date_depart')
    search_fields = ('conducteur__username', 'ville_depart', 'ville_arrivee', 'plaque_immatriculation')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('passager', 'ville_depart', 'ville_arrivee', 'date_voyage', 'places')
    list_filter = ('ville_depart', 'ville_arrivee', 'date_voyage')
    search_fields = ('passager__username', 'ville_depart', 'ville_arrivee')

@admin.register(Correspondance)
class CorrespondanceAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'demande', 'score_match', 'is_validated', 'refus_conducteur', 'refus_passager')
    list_filter = ('is_validated', 'refus_conducteur', 'refus_passager')
    search_fields = ('voyage__conducteur__username', 'demande__passager__username')

@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ('phone', 'user', 'is_verified', 'attempts', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('phone', 'user__username')
    readonly_fields = ('created_at',)

@admin.register(TripValidation)
class TripValidationAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'passenger', 'pickup_confirmed_by_driver', 'pickup_confirmed_by_passenger', 'dropoff_confirmed_by_driver', 'dropoff_confirmed_by_passenger')
    list_filter = ('pickup_confirmed_by_driver', 'pickup_confirmed_by_passenger', 'dropoff_confirmed_by_driver', 'dropoff_confirmed_by_passenger')
    readonly_fields = ('created_at', 'updated_at')
