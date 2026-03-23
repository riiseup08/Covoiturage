from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Voyage, Demande, Profile, Avis, Message
from .sms import normalize_phone, validate_african_phone
from django.utils import timezone
import re


class UserRegistrationForm(UserCreationForm):
    """Inscription avec numéro de téléphone obligatoire (email optionnel)."""
    phone = forms.CharField(
        required=True,
        max_length=20,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'placeholder': '+237 6XX XXX XXX',
            'autocomplete': 'tel',
            'type': 'tel',
        })
    )
    email = forms.EmailField(
        required=False,
        label="Adresse email (optionnel)",
        widget=forms.EmailInput(attrs={'placeholder': 'exemple@email.com', 'autocomplete': 'email'})
    )

    class Meta:
        model = User
        fields = ('username', 'phone', 'email', 'password1', 'password2')

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get('phone', ''))
        if not phone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        if not validate_african_phone(phone):
            raise forms.ValidationError("Entrez un numéro de téléphone africain valide (ex: +237 6XX XXX XXX).")
        if Profile.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Un compte existe déjà avec ce numéro de téléphone.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cette adresse email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            user.email = email
        if commit:
            user.save()
            # Save phone to profile (profile is auto-created by signal)
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=user)
            profile.phone = self.cleaned_data['phone']
            profile.save(update_fields=['phone'])
        return user


class PhoneLoginRequestForm(forms.Form):
    """Step 1: Enter phone number to receive OTP."""
    phone = forms.CharField(
        max_length=20,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'placeholder': '+237 6XX XXX XXX',
            'autocomplete': 'tel',
            'type': 'tel',
        })
    )

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get('phone', ''))
        if not phone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        if not validate_african_phone(phone):
            raise forms.ValidationError("Entrez un numéro de téléphone africain valide.")
        return phone


class PhoneOTPVerifyForm(forms.Form):
    """Step 2: Enter the OTP code received by SMS."""
    phone = forms.CharField(widget=forms.HiddenInput())
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label="Code de vérification",
        widget=forms.TextInput(attrs={
            'placeholder': '------',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'style': 'text-align: center; font-size: 24px; letter-spacing: 8px;',
        })
    )

    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code', '').strip()
        if not re.match(r'^\d{6}$', code):
            raise forms.ValidationError("Le code doit contenir exactement 6 chiffres.")
        return code


class PhoneRegisterForm(forms.Form):
    """Quick registration with phone number only (no password needed)."""
    phone = forms.CharField(
        max_length=20,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'placeholder': '+237 6XX XXX XXX',
            'autocomplete': 'tel',
            'type': 'tel',
        })
    )
    full_name = forms.CharField(
        max_length=60,
        label="Nom complet",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Jean Mbarga'})
    )

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get('phone', ''))
        if not phone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        if not validate_african_phone(phone):
            raise forms.ValidationError("Entrez un numéro de téléphone africain valide (ex: +237 6XX XXX XXX).")
        if Profile.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Un compte existe déjà avec ce numéro. Connectez-vous plutôt.")
        return phone

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("Entrez votre nom complet.")
        return name

class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ['note', 'commentaire']
        widgets = {
            'note': forms.Select(choices=[(i, f'{i} étoile(s)') for i in range(1, 6)]),
            'commentaire': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optionnel : comment s\'est passé le trajet ?', 'maxlength': 500}),
        }

class VoyageForm(forms.ModelForm):
    class Meta:
        model = Voyage
        fields = [
            'ville_depart', 'lieu_ramassage', 'ville_arrivee',
            'date_depart', 'date_arrivee', 'places_disponibles', 'prix_par_place',
            'currency', 'accept_mobile_money', 'accept_cash',
            'plaque_immatriculation', 'modele_voiture', 'type_bagage_accepte',
            'women_only',
        ]
        widgets = {
            'date_depart': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_arrivee': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'lieu_ramassage': forms.TextInput(attrs={'placeholder': 'Ex: Devant la boulangerie Saker, Rond-point...'}),
            'plaque_immatriculation': forms.TextInput(attrs={'placeholder': 'Ex: AB 1234 CD'}),
            'modele_voiture': forms.TextInput(attrs={'placeholder': 'Ex: Toyota Corolla, Peugeot 208...'}),
            'type_bagage_accepte': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_depart = cleaned_data.get("date_depart")
        date_arrivee = cleaned_data.get("date_arrivee")
        places_disponibles = cleaned_data.get("places_disponibles")
        prix_par_place = cleaned_data.get("prix_par_place")

        if date_depart and date_depart < timezone.now():
            self.add_error('date_depart', "La date de départ ne peut pas être dans le passé.")
        
        if date_depart and date_arrivee and date_arrivee < date_depart:
            self.add_error('date_arrivee', "La date d'arrivée doit être après la date de départ.")
            
        if places_disponibles is not None and places_disponibles < 1:
            self.add_error('places_disponibles', "Il doit y avoir au moins 1 place disponible.")
            
        if prix_par_place is not None and prix_par_place < 0:
            self.add_error('prix_par_place', "Le prix ne peut pas être négatif.")

        plaque = cleaned_data.get('plaque_immatriculation') or ''
        modele = cleaned_data.get('modele_voiture') or ''
        if not plaque.strip():
            self.add_error('plaque_immatriculation', "La plaque d'immatriculation est obligatoire.")
        if not modele.strip():
            self.add_error('modele_voiture', "Le modèle du véhicule est obligatoire.")

        return cleaned_data

class DemandeForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ['ville_depart', 'ville_arrivee', 'date_voyage', 'places']
        widgets = {
            'date_voyage': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def clean_date_voyage(self):
        date_voyage = self.cleaned_data.get('date_voyage')
        if date_voyage and date_voyage < timezone.now().date():
            raise forms.ValidationError("La date de voyage ne peut pas être dans le passé.")
        return date_voyage

    def clean_places(self):
        places = self.cleaned_data.get('places')
        if places is not None and places < 1:
            raise forms.ValidationError("Il faut au moins 1 place.")
        return places

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'bio', 'phone', 'is_driver', 'profile_photo',
            'whatsapp_number', 'mobile_money_number', 'mobile_money_provider',
            'gender', 'emergency_contact_name', 'emergency_contact_phone',
            'id_type', 'id_number', 'id_photo',
        ]
        widgets = {
            'profile_photo': forms.FileInput(attrs={'accept': 'image/*'}),
            'phone': forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX', 'type': 'tel'}),
            'whatsapp_number': forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX (optionnel)', 'type': 'tel'}),
            'mobile_money_number': forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX', 'type': 'tel'}),
            'mobile_money_provider': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'emergency_contact_name': forms.TextInput(attrs={'placeholder': 'Nom complet'}),
            'emergency_contact_phone': forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX', 'type': 'tel'}),
            'id_type': forms.TextInput(attrs={'placeholder': "Ex: CNI, Passeport"}),
            'id_number': forms.TextInput(attrs={'placeholder': 'Numéro du document'}),
            'id_photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Écrivez votre message...',
                'maxlength': 1000,
            }),
        }
