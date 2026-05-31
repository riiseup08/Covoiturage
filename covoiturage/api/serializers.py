from rest_framework import serializers
from django.contrib.auth.models import User
from covoiturage.models import (
    Voyage,
    Demande,
    Correspondance,
    Avis,
    Profile,
    Notification,
    Message,
    RouteAlert,
    RecurringTrip,
)
from django.db.models import Avg


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        # No email here: the user directory must not leak contact PII.
        fields = ["id", "username", "first_name", "last_name"]
        read_only_fields = ["id"]


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile model."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "bio",
            "phone",
            "is_driver",
            "profile_photo",
            "car_photo",
            "gender",
            "emergency_contact_name",
            "emergency_contact_phone",
            "referral_code",
            "id_verified",
            "driver_license_verified",
            "phone_verified",
            "trust_score",
            "created_at",
        ]
        read_only_fields = ["id", "referral_code", "trust_score", "created_at"]


class NestedProfileSerializer(serializers.ModelSerializer):
    """Driver profile embedded in (publicly listable) voyages — no contact PII.

    Phone is deliberately excluded: trips are browsable anonymously, so the
    driver's number must not ride along. Matched users get it via the
    participant-scoped CorrespondanceSerializer.contact_phone instead.
    """

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "username",
            "bio",
            "gender",
            "is_driver",
            "profile_photo",
            "car_photo",
            "id_verified",
            "driver_license_verified",
            "phone_verified",
            "trust_score",
        ]


class PublicProfileSerializer(serializers.ModelSerializer):
    """Public profile serializer with reviews."""

    username = serializers.CharField(source="user.username", read_only=True)
    note_moyenne = serializers.SerializerMethodField()
    avis_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        # Public endpoint: no email/phone. Contact details are shared only with
        # matched users (via the dashboard), not with anonymous lookups.
        fields = [
            "username",
            "bio",
            "gender",
            "is_driver",
            "profile_photo",
            "id_verified",
            "driver_license_verified",
            "trust_score",
            "note_moyenne",
            "avis_count",
        ]

    def get_note_moyenne(self, obj):
        avg = Avis.objects.filter(utilisateur_note=obj.user).aggregate(avg=Avg("note"))[
            "avg"
        ]
        return round(avg, 1) if avg else None

    def get_avis_count(self, obj):
        return Avis.objects.filter(utilisateur_note=obj.user).count()


class VoyageSerializer(serializers.ModelSerializer):
    """Serializer for Voyage model."""

    conducteur_username = serializers.CharField(
        source="conducteur.username", read_only=True
    )
    conducteur_profile = NestedProfileSerializer(source="conducteur.profile", read_only=True)

    class Meta:
        model = Voyage
        fields = [
            "id",
            "conducteur",
            "conducteur_username",
            "conducteur_profile",
            "ville_depart",
            "lieu_ramassage",
            "ville_arrivee",
            "date_depart",
            "date_arrivee",
            "places_disponibles",
            "prix_par_place",
            "plaque_immatriculation",
            "modele_voiture",
            "type_bagage_accepte",
            "women_only",
            "est_termine",
            "status",
            "start_latitude",
            "start_longitude",
            "end_latitude",
            "end_longitude",
            "created_at",
        ]
        read_only_fields = ["id", "conducteur", "created_at"]


class VoyageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating voyages."""

    class Meta:
        model = Voyage
        fields = [
            "ville_depart",
            "lieu_ramassage",
            "ville_arrivee",
            "date_depart",
            "date_arrivee",
            "places_disponibles",
            "prix_par_place",
            "plaque_immatriculation",
            "modele_voiture",
            "type_bagage_accepte",
            "women_only",
            "start_latitude",
            "start_longitude",
            "end_latitude",
            "end_longitude",
        ]

    def validate(self, data):
        from django.utils import timezone

        if data.get("date_depart") and data["date_depart"] < timezone.now():
            raise serializers.ValidationError(
                "La date de départ ne peut pas être dans le passé."
            )
        if data.get("women_only"):
            request = self.context.get("request")
            profile = getattr(getattr(request, "user", None), "profile", None)
            if not (profile and profile.is_female):
                raise serializers.ValidationError(
                    "Seules les conductrices peuvent proposer un trajet réservé aux femmes."
                )
        if data.get("date_arrivee") and data.get("date_depart"):
            if data["date_arrivee"] < data["date_depart"]:
                raise serializers.ValidationError(
                    "La date d'arrivée doit être après la date de départ."
                )
        if data.get("places_disponibles", 0) < 1:
            raise serializers.ValidationError("Il doit y avoir au moins 1 place.")
        return data


class DemandeSerializer(serializers.ModelSerializer):
    """Serializer for Demande model."""

    passager_username = serializers.CharField(
        source="passager.username", read_only=True
    )

    class Meta:
        model = Demande
        fields = [
            "id",
            "passager",
            "passager_username",
            "ville_depart",
            "ville_arrivee",
            "date_voyage",
            "places",
        ]
        read_only_fields = ["id", "passager"]


class CorrespondanceSerializer(serializers.ModelSerializer):
    """Serializer for Correspondance model."""

    voyage = VoyageSerializer(read_only=True)
    demande = DemandeSerializer(read_only=True)
    contact_phone = serializers.SerializerMethodField()

    class Meta:
        model = Correspondance
        fields = [
            "id",
            "voyage",
            "demande",
            "score_match",
            "is_validated",
            "refus_conducteur",
            "refus_passager",
            "contact_phone",
        ]

    def get_contact_phone(self, obj):
        """The other party's phone — only once the match is validated and only to
        the two participants (this viewset is already participant-scoped)."""
        request = self.context.get("request")
        if not request or not obj.is_validated:
            return None
        user = request.user
        if obj.voyage.conducteur_id == user.id:
            other = obj.demande.passager
        elif obj.demande.passager_id == user.id:
            other = obj.voyage.conducteur
        else:
            return None
        return (getattr(getattr(other, "profile", None), "phone", "") or "").strip() or None


class AvisSerializer(serializers.ModelSerializer):
    """Serializer for Avis model."""

    auteur_username = serializers.CharField(source="auteur.username", read_only=True)

    class Meta:
        model = Avis
        fields = [
            "id",
            "voyage",
            "auteur",
            "auteur_username",
            "utilisateur_note",
            "note",
            "commentaire",
            "created_at",
        ]
        read_only_fields = ["id", "auteur", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""

    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "correspondance",
            "sender",
            "sender_username",
            "content",
            "created_at",
            "is_read",
        ]
        # correspondance is taken from the URL (nested route), never the body.
        read_only_fields = ["id", "sender", "correspondance", "created_at"]


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for search query parameters."""

    ville_depart = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    ville_arrivee = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    date = serializers.DateField(required=False)
    type_baggage = serializers.ChoiceField(
        choices=["petit", "moyen", "gros", "tous"], required=False
    )
    prix_max = serializers.IntegerField(required=False, min_value=0)
    places_min = serializers.IntegerField(required=False, min_value=1)
    page = serializers.IntegerField(required=False, default=1, min_value=1)


class RouteAlertSerializer(serializers.ModelSerializer):
    """Saved-route alert ('notify me on this corridor')."""

    class Meta:
        model = RouteAlert
        fields = ["id", "ville_depart", "ville_arrivee", "active", "created_at"]
        read_only_fields = ["id", "created_at"]


class RecurringTripSerializer(serializers.ModelSerializer):
    """Weekly commute template materialized into Voyage rows by a command."""

    class Meta:
        model = RecurringTrip
        fields = [
            "id", "ville_depart", "lieu_ramassage", "ville_arrivee",
            "weekday", "heure_depart", "duree_minutes", "places_disponibles",
            "prix_par_place", "plaque_immatriculation", "modele_voiture",
            "type_bagage_accepte", "women_only", "active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
