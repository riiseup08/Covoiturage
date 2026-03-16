from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Voyage, Demande, Profile, Avis, PhoneOTP, TripValidation
from django.utils import timezone
from django.core.exceptions import ValidationError
import re


class UserRegistrationForm(UserCreationForm):
    """Registration with phone number verification (like Uber/Lyft)"""
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': '+233XXXXXXXXXX or 0XXXXXXXXXX',
            'type': 'tel',
            'autocomplete': 'tel'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        # Remove common separators and keep only digits
        phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Check minimum length (10 digits)
        if len(phone) < 10:
            raise ValidationError("Phone number must be at least 10 digits")
        
        # Check if already registered
        if Profile.objects.filter(phone=phone, phone_verified=True).exists():
            raise ValidationError("This phone number is already registered. Please login or use a different number.")
        
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        # Use phone as email temporarily (required by Django User model)
        user.email = self.cleaned_data['phone'].replace('+', '').replace('-', '') + '@covoiturage.local'
        if commit:
            user.save()
        return user

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
            'plaque_immatriculation', 'modele_voiture', 'type_bagage_accepte',
        ]
        widgets = {
            'date_depart': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_arrivee': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'lieu_ramassage': forms.TextInput(attrs={'placeholder': 'Ex: Devant la boulangerie Saker, Rond-point...'}),
            'plaque_immatriculation': forms.TextInput(attrs={'placeholder': 'Ex: AB 1234 CD'}),
            'modele_voiture': forms.TextInput(attrs={'placeholder': 'Ex: Toyota Corolla, Peugeot 208...'}),
            'type_bagage_accepte': forms.Select(attrs={'class': 'form-select'}),
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


# ========== NEW FORMS FOR PHONE OTP & PHOTOS ==========

class PhoneOTPRequestForm(forms.Form):
    """Request OTP for phone verification"""
    phone = forms.CharField(
        max_length=20,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': '+233XXXXXXXXXX or 0XXXXXXXXXX',
            'type': 'tel',
            'autocomplete': 'tel'
        })
    )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        # Remove common separators and keep only digits
        phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Check minimum length (10 digits)
        if len(phone) < 10:
            raise ValidationError("Phone number must be at least 10 digits")
        
        # Check if already verified
        from .models import Profile
        if Profile.objects.filter(phone=phone, phone_verified=True).exists():
            raise ValidationError("This phone number is already registered and verified")
        
        return phone


class PhoneOTPVerificationForm(forms.Form):
    """Verify OTP code"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label="Verification Code",
        widget=forms.TextInput(attrs={
            'placeholder': '000000',
            'type': 'text',
            'inputmode': 'numeric',
            'maxlength': '6',
            'autocomplete': 'one-time-code'
        })
    )
    
    def clean_otp_code(self):
        otp = self.cleaned_data.get('otp_code', '').strip()
        if not otp.isdigit():
            raise ValidationError("OTP must contain only numbers")
        return otp


class ProfilePhotoUploadForm(forms.ModelForm):
    """Upload profile photo"""
    class Meta:
        model = Profile
        fields = ['profile_photo']
        widgets = {
            'profile_photo': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png,image/gif',
                'class': 'form-control'
            })
        }
    
    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            # Check file size (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("Image must be smaller than 5MB")
            # Check file type
            if not photo.content_type.startswith('image/'):
                raise ValidationError("File must be an image")
        return photo


class CarPhotoUploadForm(forms.ModelForm):
    """Upload car photo"""
    class Meta:
        model = Profile
        fields = ['car_photo']
        widgets = {
            'car_photo': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png,image/gif',
                'class': 'form-control'
            })
        }
    
    def clean_car_photo(self):
        photo = self.cleaned_data.get('car_photo')
        if photo:
            # Check file size (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("Image must be smaller than 5MB")
            # Check file type
            if not photo.content_type.startswith('image/'):
                raise ValidationError("File must be an image")
        return photo


class IDVerificationForm(forms.ModelForm):
    """Upload ID for verification"""
    class Meta:
        model = Profile
        fields = ['id_type', 'id_number', 'id_photo']
        widgets = {
            'id_type': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={
                'placeholder': 'Your ID number',
                'class': 'form-control'
            }),
            'id_photo': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png,image/gif',
                'class': 'form-control'
            })
        }
    
    def clean_id_number(self):
        id_num = self.cleaned_data.get('id_number', '').strip()
        if not id_num:
            raise ValidationError("ID number is required")
        return id_num
    
    def clean_id_photo(self):
        photo = self.cleaned_data.get('id_photo')
        if not photo:
            raise ValidationError("ID photo is required")
        if photo.size > 5 * 1024 * 1024:
            raise ValidationError("Image must be smaller than 5MB")
        if not photo.content_type.startswith('image/'):
            raise ValidationError("File must be an image")
        return photo


class DriverLicenseVerificationForm(forms.ModelForm):
    """Upload driver's license for verification"""
    class Meta:
        model = Profile
        fields = ['driver_license_number', 'driver_license_expiry', 'driver_license_photo']
        widgets = {
            'driver_license_number': forms.TextInput(attrs={
                'placeholder': 'Your license number',
                'class': 'form-control'
            }),
            'driver_license_expiry': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'driver_license_photo': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png,image/gif',
                'class': 'form-control'
            })
        }
    
    def clean_driver_license_number(self):
        num = self.cleaned_data.get('driver_license_number', '').strip()
        if not num:
            raise ValidationError("License number is required")
        return num
    
    def clean_driver_license_expiry(self):
        expiry = self.cleaned_data.get('driver_license_expiry')
        if expiry and expiry < timezone.now().date():
            raise ValidationError("License has expired")
        return expiry
    
    def clean_driver_license_photo(self):
        photo = self.cleaned_data.get('driver_license_photo')
        if not photo:
            raise ValidationError("License photo is required")
        if photo.size > 5 * 1024 * 1024:
            raise ValidationError("Image must be smaller than 5MB")
        return photo


class ProfileForm(forms.ModelForm):
    """Edit user profile"""
    class Meta:
        model = Profile
        fields = ['bio', 'phone']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Tell us about yourself',
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Your phone number',
                'type': 'tel',
                'class': 'form-control',
                'readonly': 'readonly'  # Phone cannot be changed once verified
            })
        }

    def clean_places(self):
        places = self.cleaned_data.get('places')
        if places is not None and places < 1:
            raise forms.ValidationError("Il faut au moins 1 place.")
        return places

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'phone', 'is_driver']
