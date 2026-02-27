from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Voyage, Demande, Correspondance, Profile, Avis
from .forms import VoyageForm, DemandeForm, ProfileForm, AvisForm
from django.contrib.auth.forms import UserCreationForm

PAGE_SIZE = 10
SEARCH_PAGE_SIZE = 12

def landing_view(request):
    return render(request, 'voyages/landing.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # La création du profil est gérée par le signal dans models.py
            login(request, user)
            messages.success(request, "Inscription réussie ! Bienvenue sur Covoit.Africa.")
            return redirect('covoiturage:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def home_view(request):
    voyages = Voyage.objects.filter(conducteur=request.user).order_by('-date_depart')
    demandes = Demande.objects.filter(passager=request.user).order_by('-date_voyage')
    correspondances = Correspondance.objects.filter(
        Q(voyage__conducteur=request.user) | Q(demande__passager=request.user)
    ).filter(refus_conducteur=False, refus_passager=False).select_related(
        'demande', 'voyage',
        'demande__passager__profile', 'voyage__conducteur__profile'
    ).order_by('-id')

    for c in correspondances:
        other = c.demande.passager if c.voyage.conducteur == request.user else c.voyage.conducteur
        try:
            c.other_phone = (getattr(other.profile, 'phone', None) or '').strip()
        except (Profile.DoesNotExist, AttributeError):
            c.other_phone = ''

    paginator_v = Paginator(voyages, PAGE_SIZE)
    paginator_d = Paginator(demandes, PAGE_SIZE)
    paginator_c = Paginator(correspondances, PAGE_SIZE)
    page_v = request.GET.get('page_v', 1)
    page_d = request.GET.get('page_d', 1)
    page_c = request.GET.get('page_c', 1)

    context = {
        'voyages': paginator_v.get_page(page_v),
        'demandes': paginator_d.get_page(page_d),
        'correspondances': paginator_c.get_page(page_c),
    }
    return render(request, 'voyages/dashboard.html', context)

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('covoiturage:dashboard')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'voyages/profile.html', {'form': form})

@login_required
def public_profile_view(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    avis_list = Avis.objects.filter(utilisateur_note=profile.user).select_related('auteur', 'voyage').order_by('-created_at')[:20]
    from django.db.models import Avg
    note_moyenne = Avis.objects.filter(utilisateur_note=profile.user).aggregate(avg=Avg('note'))['avg']
    avis_count = Avis.objects.filter(utilisateur_note=profile.user).count()
    context = {'profile': profile, 'avis_list': avis_list, 'note_moyenne': note_moyenne, 'avis_count': avis_count}
    return render(request, 'voyages/public_profile.html', context)

@login_required
def add_voyage(request):
    if request.method == 'POST':
        form = VoyageForm(request.POST)
        if form.is_valid():
            voyage = form.save(commit=False)
            voyage.conducteur = request.user
            voyage.save()
            messages.success(request, 'Votre trajet a été publié avec succès.')
            return redirect('covoiturage:dashboard')
    else:
        form = VoyageForm()
    return render(request, 'voyages/add_voyage.html', {'form': form})

@login_required
def add_demande(request):
    if request.method == 'POST':
        form = DemandeForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.passager = request.user
            demande.save()
            messages.success(request, 'Votre demande a été publiée avec succès.')
            return redirect('covoiturage:dashboard')
    else:
        form = DemandeForm()
    return render(request, 'voyages/add_demande.html', {'form': form})

@login_required
def edit_voyage(request, voyage_id):
    voyage = get_object_or_404(Voyage, id=voyage_id, conducteur=request.user)
    if request.method == 'POST':
        form = VoyageForm(request.POST, instance=voyage)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trajet modifié avec succès.')
            return redirect('covoiturage:dashboard')
    else:
        form = VoyageForm(instance=voyage)
    return render(request, 'voyages/edit_voyage.html', {'form': form})

@login_required
def delete_voyage(request, voyage_id):
    voyage = get_object_or_404(Voyage, id=voyage_id, conducteur=request.user)
    if request.method == 'POST':
        voyage.delete()
        messages.success(request, 'Trajet supprimé.')
        return redirect('covoiturage:dashboard')
    return render(request, 'voyages/confirm_delete.html', {'object': voyage, 'type': 'Trajet'})

@login_required
def edit_demande(request, demande_id):
    demande = get_object_or_404(Demande, id=demande_id, passager=request.user)
    if request.method == 'POST':
        form = DemandeForm(request.POST, instance=demande)
        if form.is_valid():
            form.save()
            messages.success(request, 'Demande modifiée avec succès.')
            return redirect('covoiturage:dashboard')
    else:
        form = DemandeForm(instance=demande)
    return render(request, 'voyages/edit_demande.html', {'form': form})

@login_required
def delete_demande(request, demande_id):
    demande = get_object_or_404(Demande, id=demande_id, passager=request.user)
    if request.method == 'POST':
        demande.delete()
        messages.success(request, 'Demande supprimée.')
        return redirect('covoiturage:dashboard')
    return render(request, 'voyages/confirm_delete.html', {'object': demande, 'type': 'Demande'})

@login_required
def validate_correspondance(request, correspondance_id):
    correspondance = get_object_or_404(Correspondance, id=correspondance_id, voyage__conducteur=request.user)
    if request.method == 'POST':
        if not correspondance.is_validated:
            correspondance.is_validated = True
            correspondance.save()
            messages.success(request, f"Vous avez validé le trajet avec {correspondance.demande.passager.username}.")
        return redirect('covoiturage:dashboard')
    return redirect('covoiturage:dashboard')


@login_required
def refuse_correspondance(request, correspondance_id):
    """Le conducteur refuse ce match."""
    correspondance = get_object_or_404(Correspondance, id=correspondance_id, voyage__conducteur=request.user)
    if request.method == 'POST':
        if not correspondance.is_validated and not correspondance.refus_conducteur:
            correspondance.refus_conducteur = True
            correspondance.save()
            messages.info(request, "Vous avez refusé ce match.")
        return redirect('covoiturage:dashboard')
    return redirect('covoiturage:dashboard')


@login_required
def cancel_correspondance(request, correspondance_id):
    """Le passager annule son intérêt pour ce match."""
    correspondance = get_object_or_404(Correspondance, id=correspondance_id, demande__passager=request.user)
    if request.method == 'POST':
        if not correspondance.refus_passager:
            correspondance.refus_passager = True
            correspondance.save()
            messages.info(request, "Vous avez annulé votre intérêt pour ce trajet.")
        return redirect('covoiturage:dashboard')
    return redirect('covoiturage:dashboard')


@login_required
def mark_voyage_termine(request, voyage_id):
    """Marquer un trajet comme terminé (masqué des recherches)."""
    voyage = get_object_or_404(Voyage, id=voyage_id, conducteur=request.user)
    if request.method == 'POST':
        voyage.est_termine = True
        voyage.save()
        messages.success(request, "Trajet marqué comme terminé.")
        return redirect('covoiturage:dashboard')
    return redirect('covoiturage:dashboard')


@login_required
def search_trajets(request):
    """Recherche de trajets avec filtres et pagination."""
    voyages = Voyage.objects.filter(
        date_depart__gte=timezone.now(),
        places_disponibles__gte=1,
        est_termine=False
    ).exclude(conducteur=request.user).select_related('conducteur').order_by('date_depart')

    ville_depart = request.GET.get('ville_depart', '').strip()
    ville_arrivee = request.GET.get('ville_arrivee', '').strip()
    date_str = request.GET.get('date', '').strip()
    type_bagage = request.GET.get('type_bagage', '').strip()
    try:
        prix_max = request.GET.get('prix_max')
        prix_max = int(prix_max) if prix_max else None
    except ValueError:
        prix_max = None
    try:
        places_min = request.GET.get('places_min')
        places_min = int(places_min) if places_min else None
    except ValueError:
        places_min = None

    if ville_depart:
        voyages = voyages.filter(ville_depart__icontains=ville_depart)
    if ville_arrivee:
        voyages = voyages.filter(ville_arrivee__icontains=ville_arrivee)
    if date_str:
        try:
            from datetime import datetime
            search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            voyages = voyages.filter(date_depart__date=search_date)
        except ValueError:
            pass
    if type_bagage and type_bagage in dict(Voyage.BAGAGE_CHOICES):
        voyages = voyages.filter(type_bagage_accepte=type_bagage)
    if prix_max is not None:
        voyages = voyages.filter(prix_par_place__lte=prix_max)
    if places_min is not None:
        voyages = voyages.filter(places_disponibles__gte=places_min)

    paginator = Paginator(voyages, SEARCH_PAGE_SIZE)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    context = {
        'voyages': page_obj,
        'ville_depart': ville_depart,
        'ville_arrivee': ville_arrivee,
        'date': date_str,
        'type_bagage': type_bagage,
        'prix_max': prix_max,
        'places_min': places_min,
        'Voyage': Voyage,
    }
    return render(request, 'voyages/search_trajets.html', context)


def _get_can_rate_list(user):
    """Trajets terminés où l'utilisateur peut encore laisser un avis (par voyage, autre utilisateur)."""
    from django.db.models import Q
    # Voyages terminés où user est conducteur
    as_conducteur = Voyage.objects.filter(conducteur=user, est_termine=True)
    # Voyages terminés où user est passager (correspondance validée)
    as_passager = Voyage.objects.filter(
        est_termine=True,
        correspondance__demande__passager=user,
        correspondance__is_validated=True,
        correspondance__refus_conducteur=False,
        correspondance__refus_passager=False
    ).distinct()
    opportunities = []
    seen = set()
    for v in as_conducteur:
        for c in v.correspondance_set.filter(is_validated=True, refus_conducteur=False, refus_passager=False).select_related('demande__passager'):
            other = c.demande.passager_id
            if (v.id, other) not in seen:
                seen.add((v.id, other))
                if not Avis.objects.filter(voyage=v, auteur=user, utilisateur_note_id=other).exists():
                    opportunities.append((v, c.demande.passager))
    for v in as_passager:
        other = v.conducteur_id
        if (v.id, other) not in seen:
            seen.add((v.id, other))
            if not Avis.objects.filter(voyage=v, auteur=user, utilisateur_note_id=other).exists():
                opportunities.append((v, v.conducteur))
    return opportunities


@login_required
def avis_list_view(request):
    """Liste des trajets pour lesquels l'utilisateur peut encore laisser un avis."""
    opportunities = _get_can_rate_list(request.user)
    context = {'opportunities': opportunities}
    return render(request, 'voyages/avis_list.html', context)


@login_required
def add_avis_view(request, voyage_id, user_id):
    """Déposer un avis pour un trajet terminé (sur l'autre participant)."""
    voyage = get_object_or_404(Voyage, id=voyage_id, est_termine=True)
    utilisateur_note = get_object_or_404(User, id=user_id)
    if request.user.id == utilisateur_note.id:
        messages.error(request, "Vous ne pouvez pas vous noter vous-même.")
        return redirect('covoiturage:avis_list')
    # Vérifier que request.user a bien participé à ce trajet avec utilisateur_note
    can_rate = False
    if voyage.conducteur == request.user:
        can_rate = Correspondance.objects.filter(
            voyage=voyage, demande__passager=utilisateur_note,
            is_validated=True, refus_conducteur=False, refus_passager=False
        ).exists()
    elif voyage.conducteur == utilisateur_note:
        can_rate = Correspondance.objects.filter(
            voyage=voyage, demande__passager=request.user,
            is_validated=True, refus_conducteur=False, refus_passager=False
        ).exists()
    if not can_rate:
        messages.error(request, "Vous ne pouvez pas noter cette personne pour ce trajet.")
        return redirect('covoiturage:avis_list')
    if Avis.objects.filter(voyage=voyage, auteur=request.user, utilisateur_note=utilisateur_note).exists():
        messages.warning(request, "Vous avez déjà laissé un avis pour cette personne sur ce trajet.")
        return redirect('covoiturage:avis_list')
    if request.method == 'POST':
        form = AvisForm(request.POST)
        if form.is_valid():
            avis = form.save(commit=False)
            avis.voyage = voyage
            avis.auteur = request.user
            avis.utilisateur_note = utilisateur_note
            avis.save()
            messages.success(request, f"Merci ! Votre avis sur {utilisateur_note.username} a été enregistré.")
            return redirect('covoiturage:avis_list')
    else:
        form = AvisForm()
    context = {'form': form, 'voyage': voyage, 'utilisateur_note': utilisateur_note}
    return render(request, 'voyages/add_avis.html', context)
