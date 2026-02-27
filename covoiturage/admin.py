from django.contrib import admin
from .models import Profile, Voyage, Demande, Correspondance, Avis

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'utilisateur_note', 'voyage', 'note', 'created_at')
    list_filter = ('note', 'created_at')
    search_fields = ('auteur__username', 'utilisateur_note__username', 'commentaire')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # 'ville' et 'pays' ont été enlevés car ils n'existent plus dans Profile
    list_display = ('user', 'phone', 'is_driver')
    list_filter = ('is_driver',)
    search_fields = ('user__username', 'phone')

@admin.register(Voyage)
class VoyageAdmin(admin.ModelAdmin):
    list_display = ('conducteur', 'ville_depart', 'ville_arrivee', 'date_depart', 'places_disponibles', 'prix_par_place')
    list_filter = ('ville_depart', 'ville_arrivee', 'date_depart')
    search_fields = ('conducteur__username', 'ville_depart', 'ville_arrivee')

@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('passager', 'ville_depart', 'ville_arrivee', 'date_voyage', 'places')
    list_filter = ('ville_depart', 'ville_arrivee', 'date_voyage')
    search_fields = ('passager__username', 'ville_depart', 'ville_arrivee')

@admin.register(Correspondance)
class CorrespondanceAdmin(admin.ModelAdmin):
    # 'passager_embarque' et 'paiement_effectue' ont été enlevés
    list_display = ('voyage', 'demande', 'score_match', 'is_validated')
    list_filter = ('is_validated',)
