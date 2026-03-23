from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Profile, Voyage, Demande, Correspondance,
    Avis, Notification, Message, Payment,
)


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'email', 'bio', 'phone', 'is_driver',
            'profile_photo', 'car_photo',
            'id_type', 'id_number', 'id_verified',
            'driver_license_number', 'driver_license_verified',
            'phone_verified',
            'whatsapp_number', 'mobile_money_number', 'mobile_money_provider',
            'preferred_language',
            'gender', 'emergency_contact_name', 'emergency_contact_phone',
            'trust_score', 'created_at',
        ]
        read_only_fields = ['id_verified', 'driver_license_verified', 'phone_verified', 'trust_score']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'bio', 'phone', 'is_driver',
            'whatsapp_number', 'mobile_money_number', 'mobile_money_provider',
            'preferred_language',
            'gender', 'emergency_contact_name', 'emergency_contact_phone',
        ]


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=30, required=False, default='')
    last_name = serializers.CharField(max_length=150, required=False, default='')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class VoyageSerializer(serializers.ModelSerializer):
    conducteur_username = serializers.CharField(source='conducteur.username', read_only=True)
    conducteur_phone = serializers.SerializerMethodField()
    conducteur_gender = serializers.SerializerMethodField()

    class Meta:
        model = Voyage
        fields = [
            'id', 'conducteur', 'conducteur_username', 'conducteur_phone', 'conducteur_gender',
            'ville_depart', 'lieu_ramassage', 'ville_arrivee',
            'date_depart', 'date_arrivee',
            'places_disponibles', 'prix_par_place', 'currency',
            'accept_mobile_money', 'accept_cash',
            'plaque_immatriculation', 'modele_voiture', 'type_bagage_accepte',
            'start_latitude', 'start_longitude', 'end_latitude', 'end_longitude',
            'women_only', 'est_termine', 'status',
            'created_at',
        ]
        read_only_fields = ['conducteur', 'start_latitude', 'start_longitude', 'end_latitude', 'end_longitude', 'created_at']

    def get_conducteur_phone(self, obj):
        profile = getattr(obj.conducteur, 'profile', None)
        return profile.phone if profile else None

    def get_conducteur_gender(self, obj):
        profile = getattr(obj.conducteur, 'profile', None)
        return profile.gender if profile else ''


class VoyageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voyage
        fields = [
            'ville_depart', 'lieu_ramassage', 'ville_arrivee',
            'date_depart', 'date_arrivee',
            'places_disponibles', 'prix_par_place', 'currency',
            'accept_mobile_money', 'accept_cash',
            'plaque_immatriculation', 'modele_voiture', 'type_bagage_accepte',
            'women_only',
        ]


class DemandeSerializer(serializers.ModelSerializer):
    passager_username = serializers.CharField(source='passager.username', read_only=True)

    class Meta:
        model = Demande
        fields = ['id', 'passager', 'passager_username', 'ville_depart', 'ville_arrivee', 'date_voyage', 'places']
        read_only_fields = ['passager']


class CorrespondanceSerializer(serializers.ModelSerializer):
    voyage = VoyageSerializer(read_only=True)
    demande = DemandeSerializer(read_only=True)

    class Meta:
        model = Correspondance
        fields = ['id', 'voyage', 'demande', 'score_match', 'is_validated', 'refus_conducteur', 'refus_passager']


class AvisSerializer(serializers.ModelSerializer):
    auteur_username = serializers.CharField(source='auteur.username', read_only=True)
    utilisateur_note_username = serializers.CharField(source='utilisateur_note.username', read_only=True)

    class Meta:
        model = Avis
        fields = ['id', 'voyage', 'auteur', 'auteur_username', 'utilisateur_note', 'utilisateur_note_username', 'note', 'commentaire', 'created_at']
        read_only_fields = ['auteur']


class NotificationSerializer(serializers.ModelSerializer):
    icon = serializers.ReadOnlyField()

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'icon', 'related_voyage', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'correspondance', 'sender', 'sender_username', 'content', 'created_at']
        read_only_fields = ['sender']


class PaymentSerializer(serializers.ModelSerializer):
    payer_username = serializers.CharField(source='payer.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'correspondance', 'payer', 'payer_username',
            'receiver', 'receiver_username',
            'amount', 'currency', 'method', 'provider',
            'phone_number', 'status', 'transaction_ref',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['payer', 'receiver', 'status', 'transaction_ref']


class PaymentCreateSerializer(serializers.Serializer):
    correspondance_id = serializers.IntegerField()
    method = serializers.ChoiceField(choices=['mobile_money', 'cash'])
    provider = serializers.ChoiceField(choices=['mtn', 'orange', 'moov', 'airtel', 'wave', 'cash'], required=False, default='')
    phone_number = serializers.CharField(max_length=20, required=False, default='')
