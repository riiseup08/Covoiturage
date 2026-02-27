from django import forms
from .models import Voyage, Demande, Profile, Avis
from django.utils import timezone

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

    def clean_places(self):
        places = self.cleaned_data.get('places')
        if places is not None and places < 1:
            raise forms.ValidationError("Il faut au moins 1 place.")
        return places

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'phone', 'is_driver']
