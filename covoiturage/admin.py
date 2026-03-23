from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, Voyage, Demande, Correspondance, Avis, Message, PhoneOTP

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'utilisateur_note', 'voyage', 'note', 'created_at')
    list_filter = ('note', 'created_at')
    search_fields = ('auteur__username', 'utilisateur_note__username', 'commentaire')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'phone_verified', 'is_driver', 'id_verified', 'gender', 'id_type_display')
    list_filter = ('is_driver', 'phone_verified', 'id_verified', 'gender', 'mobile_money_provider')
    search_fields = ('user__username', 'phone', 'whatsapp_number', 'mobile_money_number', 'id_number')
    readonly_fields = ('id_photo_preview',)
    actions = ['approve_id_verification', 'reject_id_verification']

    def id_type_display(self, obj):
        if obj.id_type and obj.id_number:
            return f"{obj.id_type} ({obj.id_number[:6]}...)"
        return "-"
    id_type_display.short_description = "Document ID"

    def id_photo_preview(self, obj):
        if obj.id_photo:
            return format_html('<img src="{}" style="max-width:400px; max-height:300px;" />', obj.id_photo.url)
        return "Aucune photo"
    id_photo_preview.short_description = "Aperçu du document"

    @admin.action(description="✅ Approuver la vérification d'identité")
    def approve_id_verification(self, request, queryset):
        updated = queryset.filter(id_type__gt='', id_number__gt='').update(
            id_verified=True,
            verification_status='verified',
            verification_notes='Identité vérifiée par admin',
        )
        self.message_user(request, f"{updated} profil(s) vérifié(s) avec succès.")

    @admin.action(description="❌ Rejeter la vérification d'identité")
    def reject_id_verification(self, request, queryset):
        updated = queryset.update(
            id_verified=False,
            verification_status='rejected',
            verification_notes='Document rejeté par admin – veuillez soumettre un document valide.',
        )
        self.message_user(request, f"{updated} profil(s) rejeté(s).")

@admin.register(Voyage)
class VoyageAdmin(admin.ModelAdmin):
    list_display = ('conducteur', 'ville_depart', 'ville_arrivee', 'date_depart', 'places_disponibles', 'prix_par_place', 'women_only')
    list_filter = ('ville_depart', 'ville_arrivee', 'date_depart', 'women_only')
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

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'correspondance', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'content')

@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'created_at', 'is_used', 'attempts')
    list_filter = ('is_used', 'created_at')
    search_fields = ('phone',)
    readonly_fields = ('code',)
