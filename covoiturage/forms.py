from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Voyage, Demande, Profile, Avis, Message
from django.utils import timezone


class UserRegistrationForm(UserCreationForm):
    """Inscription avec email obligatoire."""
    email = forms.EmailField(
        required=True,
        label="Adresse email",
        widget=forms.EmailInput(attrs={'placeholder': 'exemple@email.com', 'autocomplete': 'email'})
    )
    referral_code = forms.CharField(
        required=False,
        label="Code de parrainage (optionnel)",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: ABC1234'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cette adresse email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].strip().lower()
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
            'women_only',
        ]
        widgets = {
            'date_depart': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_arrivee': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'lieu_ramassage': forms.TextInput(attrs={'placeholder': 'Ex: Devant la boulangerie Saker, Rond-point...'}),
            'plaque_immatriculation': forms.TextInput(attrs={'placeholder': 'Ex: AB 1234 CD'}),
            'modele_voiture': forms.TextInput(attrs={'placeholder': 'Ex: Toyota Corolla, Peugeot 208...'}),
            'type_bagage_accepte': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        # Only a female driver may offer a women-only ride.
        if cleaned_data.get('women_only') and self._user is not None:
            profile = getattr(self._user, 'profile', None)
            if not (profile and profile.is_female):
                self.add_error(
                    'women_only',
                    "Seules les conductrices peuvent proposer un trajet réservé aux femmes.",
                )
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
            'gender', 'emergency_contact_name', 'emergency_contact_phone',
        ]
        widgets = {
            'profile_photo': forms.FileInput(attrs={'accept': 'image/*'}),
            'emergency_contact_name': forms.TextInput(attrs={'placeholder': "Ex: Marie (sœur)"}),
            'emergency_contact_phone': forms.TextInput(attrs={'placeholder': 'Ex: 6XX XX XX XX'}),
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
