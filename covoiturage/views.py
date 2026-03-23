from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderServiceError
from .models import Voyage, Demande, Correspondance, Profile, Avis, Notification, Message, PhoneOTP
from .forms import (
    VoyageForm, DemandeForm, ProfileForm, AvisForm, UserRegistrationForm, MessageForm,
    PhoneLoginRequestForm, PhoneOTPVerifyForm, PhoneRegisterForm,
)
from .sms import send_otp_sms, normalize_phone
from .notifications import get_unread_count, mark_all_read

PAGE_SIZE = 10
SEARCH_PAGE_SIZE = 12

_geocoder = Nominatim(
    user_agent=settings.NOMINATIM_USER_AGENT,
    timeout=settings.NOMINATIM_TIMEOUT,
)
_geocode = RateLimiter(_geocoder.geocode, min_delay_seconds=settings.NOMINATIM_MIN_DELAY)
_reverse = RateLimiter(_geocoder.reverse, min_delay_seconds=settings.NOMINATIM_MIN_DELAY)

import json as _json
import logging
_logger = logging.getLogger(__name__)


def _geocode_voyage(voyage):
    """Auto-geocode departure and arrival cities into lat/lon fields."""
    for prefix, city_field in [('start', 'ville_depart'), ('end', 'ville_arrivee')]:
        city = getattr(voyage, city_field, '')
        if not city:
            continue
        # Skip if already has coordinates and city hasn't changed
        lat_field = f'{prefix}_latitude'
        lon_field = f'{prefix}_longitude'
        try:
            loc = _geocode(city + ', Africa', exactly_one=True, language='fr')
            if loc:
                setattr(voyage, lat_field, loc.latitude)
                setattr(voyage, lon_field, loc.longitude)
        except GeocoderServiceError:
            _logger.warning("Geocoding failed for %s", city)


def landing_view(request):
    return render(request, 'voyages/landing.html')


def custom_404(request, exception=None):
    if getattr(request, 'user', None) is not None and request.user.is_authenticated:
        return render(request, '404.html', status=404)
    return render(request, '404.html', status=404)


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('covoiturage:dashboard')  
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


# ── Phone OTP Authentication ──────────────────────────────────────────

def phone_login_view(request):
    """Step 1: User enters phone number to receive OTP."""
    if request.user.is_authenticated:
        return redirect('covoiturage:dashboard')

    if request.method == 'POST':
        form = PhoneLoginRequestForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            # Check if a user exists with this phone
            profile = Profile.objects.filter(phone=phone).first()
            if not profile:
                form.add_error('phone', "Aucun compte trouvé avec ce numéro. Inscrivez-vous d'abord.")
                return render(request, 'registration/phone_login.html', {'form': form})
            # Generate and send OTP
            otp = PhoneOTP.generate(phone)
            send_otp_sms(phone, otp.code)
            request.session['otp_phone'] = phone
            request.session['otp_action'] = 'login'
            return redirect('covoiturage:phone_verify_otp')
    else:
        form = PhoneLoginRequestForm()
    return render(request, 'registration/phone_login.html', {'form': form})


def phone_register_view(request):
    """Quick registration with phone number (no password)."""
    if request.user.is_authenticated:
        return redirect('covoiturage:dashboard')

    if request.method == 'POST':
        form = PhoneRegisterForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            full_name = form.cleaned_data['full_name']
            # Generate and send OTP
            otp = PhoneOTP.generate(phone)
            send_otp_sms(phone, otp.code)
            request.session['otp_phone'] = phone
            request.session['otp_full_name'] = full_name
            request.session['otp_action'] = 'register'
            return redirect('covoiturage:phone_verify_otp')
    else:
        form = PhoneRegisterForm()
    return render(request, 'registration/phone_register.html', {'form': form})


def phone_verify_otp_view(request):
    """Step 2: User enters the OTP code received by SMS."""
    phone = request.session.get('otp_phone')
    action = request.session.get('otp_action', 'login')
    if not phone:
        return redirect('covoiturage:phone_login')

    if request.method == 'POST':
        form = PhoneOTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            submitted_phone = normalize_phone(form.cleaned_data['phone'])

            # Ensure the phone in the form matches the session
            if submitted_phone != phone:
                form.add_error(None, "Numéro de téléphone invalide.")
                return render(request, 'registration/phone_verify_otp.html', {
                    'form': form, 'phone': phone, 'action': action
                })

            if action == 'register':
                # For registration, verify OTP then create user
                if not PhoneOTP.verify(phone, otp_code):
                    form.add_error('otp_code', "Code incorrect ou expiré. Réessayez.")
                    return render(request, 'registration/phone_verify_otp.html', {
                        'form': form, 'phone': phone, 'action': action
                    })
                full_name = request.session.get('otp_full_name', '')
                parts = full_name.split(maxsplit=1)
                first_name = parts[0] if parts else full_name
                last_name = parts[1] if len(parts) > 1 else ''
                # Generate username from phone (last 8 digits)
                import secrets
                username = f"user_{phone[-8:]}_{secrets.token_hex(2)}"
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                user.set_unusable_password()
                user.save()
                try:
                    profile = user.profile
                except Profile.DoesNotExist:
                    profile = Profile.objects.create(user=user)
                profile.phone = phone
                profile.phone_verified = True
                profile.save(update_fields=['phone', 'phone_verified'])
                # Clean session
                for key in ('otp_phone', 'otp_full_name', 'otp_action'):
                    request.session.pop(key, None)
                login(request, user, backend='covoiturage.backends.PhoneOTPBackend')
                messages.success(request, f"Bienvenue {first_name} ! Votre compte a été créé.")
                return redirect('covoiturage:dashboard')
            else:
                # Login: authenticate via PhoneOTPBackend
                user = authenticate(request, phone=phone, otp_code=otp_code)
                if user:
                    for key in ('otp_phone', 'otp_action'):
                        request.session.pop(key, None)
                    login(request, user, backend='covoiturage.backends.PhoneOTPBackend')
                    return redirect('covoiturage:dashboard')
                else:
                    form.add_error('otp_code', "Code incorrect ou expiré. Réessayez.")
    else:
        form = PhoneOTPVerifyForm(initial={'phone': phone})

    return render(request, 'registration/phone_verify_otp.html', {
        'form': form, 'phone': phone, 'action': action
    })


def phone_resend_otp_view(request):
    """Resend OTP code to the phone number in session."""
    phone = request.session.get('otp_phone')
    if not phone:
        return redirect('covoiturage:phone_login')
    otp = PhoneOTP.generate(phone)
    send_otp_sms(phone, otp.code)
    messages.info(request, "Un nouveau code a été envoyé à votre numéro.")
    return redirect('covoiturage:phone_verify_otp')

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
    from django.db.models import Avg
    other_ids = set()
    for c in correspondances:
        o = c.demande.passager_id if c.voyage.conducteur_id == request.user.id else c.voyage.conducteur_id
        other_ids.add(o)
    notes_qs = Avis.objects.filter(utilisateur_note_id__in=other_ids).values('utilisateur_note_id').annotate(avg=Avg('note'))
    notes_dict = {n['utilisateur_note_id']: n['avg'] for n in notes_qs}
    for c in correspondances:
        other_id = c.demande.passager_id if c.voyage.conducteur_id == request.user.id else c.voyage.conducteur_id
        c.other_note_moyenne = notes_dict.get(other_id)

    paginator_v = Paginator(voyages, PAGE_SIZE)
    paginator_d = Paginator(demandes, PAGE_SIZE)
    paginator_c = Paginator(correspondances, PAGE_SIZE)
    page_v = request.GET.get('page_v', 1)
    page_d = request.GET.get('page_d', 1)
    page_c = request.GET.get('page_c', 1)

    # Personal analytics
    from django.db.models import Sum, Avg
    completed_trips = Voyage.objects.filter(conducteur=request.user, est_termine=True).count()
    completed_as_passenger = Correspondance.objects.filter(
        demande__passager=request.user, is_validated=True,
        refus_conducteur=False, refus_passager=False,
        voyage__est_termine=True
    ).count()
    total_earnings = Voyage.objects.filter(
        conducteur=request.user, est_termine=True
    ).aggregate(total=Sum('prix_par_place'))['total'] or 0
    avg_rating_received = Avis.objects.filter(
        utilisateur_note=request.user
    ).aggregate(avg=Avg('note'))['avg']
    total_reviews_received = Avis.objects.filter(utilisateur_note=request.user).count()

    context = {
        'voyages': paginator_v.get_page(page_v),
        'demandes': paginator_d.get_page(page_d),
        'correspondances': paginator_c.get_page(page_c),
        'stats': {
            'total_voyages': voyages.count(),
            'total_demandes': demandes.count(),
            'total_correspondances': correspondances.count(),
            'completed_trips': completed_trips,
            'completed_as_passenger': completed_as_passenger,
            'total_earnings': total_earnings,
            'avg_rating': avg_rating_received,
            'total_reviews': total_reviews_received,
        },
        'unread_count': get_unread_count(request.user),
    }
    return render(request, 'voyages/dashboard.html', context)

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('covoiturage:profile')
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
    is_female = getattr(request.user, 'profile', None) and request.user.profile.gender == 'female'
    if request.method == 'POST':
        form = VoyageForm(request.POST)
        if form.is_valid():
            voyage = form.save(commit=False)
            voyage.conducteur = request.user
            if not is_female:
                voyage.women_only = False
            _geocode_voyage(voyage)
            voyage.save()
            messages.success(request, 'Votre trajet a été publié avec succès.')
            return redirect('covoiturage:dashboard')
    else:
        form = VoyageForm()
    return render(request, 'voyages/add_voyage.html', {'form': form, 'is_female': is_female})

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
        initial = {}
        if request.GET.get('ville_depart'):
            initial['ville_depart'] = request.GET['ville_depart']
        if request.GET.get('ville_arrivee'):
            initial['ville_arrivee'] = request.GET['ville_arrivee']
        form = DemandeForm(initial=initial)
    return render(request, 'voyages/add_demande.html', {'form': form})

@login_required
def edit_voyage(request, voyage_id):
    voyage = get_object_or_404(Voyage, id=voyage_id, conducteur=request.user)
    is_female = getattr(request.user, 'profile', None) and request.user.profile.gender == 'female'
    if request.method == 'POST':
        old_depart = voyage.ville_depart
        old_arrivee = voyage.ville_arrivee
        form = VoyageForm(request.POST, instance=voyage)
        if form.is_valid():
            voyage = form.save(commit=False)
            if not is_female:
                voyage.women_only = False
            if voyage.ville_depart != old_depart or voyage.ville_arrivee != old_arrivee:
                _geocode_voyage(voyage)
            voyage.save()
            messages.success(request, 'Trajet modifié avec succès.')
            return redirect('covoiturage:dashboard')
    else:
        form = VoyageForm(instance=voyage)
    return render(request, 'voyages/edit_voyage.html', {'form': form, 'is_female': is_female})

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
            # Decrement available seats
            voyage = correspondance.voyage
            places_needed = correspondance.demande.places
            if voyage.places_disponibles >= places_needed:
                voyage.places_disponibles -= places_needed
                voyage.save(update_fields=['places_disponibles'])
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
def geocode_forward(request):
    """Recherche d'adresse via Nominatim (OpenStreetMap)."""
    query = (request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({'results': []})
    try:
        locations = _geocode(
            query,
            exactly_one=False,
            addressdetails=True,
            language=settings.NOMINATIM_LANGUAGE,
            limit=5,
        )
    except GeocoderServiceError:
        return JsonResponse({'error': 'geocoding_failed'}, status=503)
    if not locations:
        return JsonResponse({'results': []})
    results = [
        {
            'display_name': loc.address,
            'lat': float(loc.latitude),
            'lon': float(loc.longitude),
        }
        for loc in locations
    ]
    return JsonResponse({'results': results})


@login_required
def geocode_reverse(request):
    """Inverse: coord -> adresse via Nominatim."""
    try:
        lat = float(request.GET.get('lat', ''))
        lon = float(request.GET.get('lon', ''))
    except ValueError:
        return JsonResponse({'error': 'invalid_coordinates'}, status=400)
    try:
        location = _reverse(
            (lat, lon),
            exactly_one=True,
            addressdetails=True,
            language=settings.NOMINATIM_LANGUAGE,
        )
    except GeocoderServiceError:
        return JsonResponse({'error': 'geocoding_failed'}, status=503)
    if not location:
        return JsonResponse({'results': []})
    result = {
        'display_name': location.address,
        'lat': float(location.latitude),
        'lon': float(location.longitude),
    }
    return JsonResponse({'results': [result]})


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
    women_only = request.GET.get('women_only', '').strip()
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
    if women_only == '1':
        voyages = voyages.filter(women_only=True)

    paginator = Paginator(voyages, SEARCH_PAGE_SIZE)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    # Build geo data for map
    map_markers = []
    for v in page_obj:
        if v.start_latitude and v.start_longitude:
            map_markers.append({
                'id': v.id,
                'depart': v.ville_depart,
                'arrivee': v.ville_arrivee,
                'start_lat': v.start_latitude,
                'start_lon': v.start_longitude,
                'end_lat': v.end_latitude,
                'end_lon': v.end_longitude,
                'conducteur': v.conducteur.username,
                'prix': str(v.prix_par_place),
                'places': v.places_disponibles,
                'date': v.date_depart.strftime('%d %b %Y %H:%M'),
                'women_only': v.women_only,
            })

    context = {
        'voyages': page_obj,
        'ville_depart': ville_depart,
        'ville_arrivee': ville_arrivee,
        'date': date_str,
        'type_bagage': type_bagage,
        'prix_max': prix_max,
        'places_min': places_min,
        'women_only': women_only,
        'Voyage': Voyage,
        'map_markers_json': _json.dumps(map_markers),
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


# ================== NOTIFICATIONS VIEWS ==================

@login_required
def notifications_list(request):
    """Affiche la liste des notifications de l'utilisateur."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'notifications': page_obj,
        'unread_count': get_unread_count(request.user),
    }
    return render(request, 'voyages/notifications_list.html', context)


@login_required
@require_POST
def notifications_mark_read(request, notification_id):
    """Marquer une notification comme lue (POST only)."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Redirect to the related object if available
    if notification.related_voyage:
        return redirect('covoiturage:dashboard')
    elif notification.related_avis:
        return redirect('covoiturage:avis_list')
    
    return redirect('covoiturage:notifications_list')


@login_required
def notifications_mark_all_read(request):
    """Marquer toutes les notifications comme lues."""
    if request.method == 'POST':
        mark_all_read(request.user)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
    return redirect('covoiturage:notifications_list')


# ================== MESSAGING VIEWS ==================

@login_required
def conversation_view(request, correspondance_id):
    """Chat thread for a validated match."""
    correspondance = get_object_or_404(Correspondance, id=correspondance_id)

    # Only the driver or passenger involved may access
    is_driver = correspondance.voyage.conducteur == request.user
    is_passenger = correspondance.demande.passager == request.user
    if not (is_driver or is_passenger):
        messages.error(request, "Vous n'avez pas accès à cette conversation.")
        return redirect('covoiturage:dashboard')

    if not correspondance.is_validated:
        messages.info(request, "La conversation sera disponible une fois le match validé.")
        return redirect('covoiturage:dashboard')

    other_user = correspondance.demande.passager if is_driver else correspondance.voyage.conducteur

    # Mark incoming messages as read
    Message.objects.filter(
        correspondance=correspondance, is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.correspondance = correspondance
            msg.sender = request.user
            msg.save()
            return redirect('covoiturage:conversation', correspondance_id=correspondance.id)
    else:
        form = MessageForm()

    msgs = correspondance.messages.select_related('sender').order_by('created_at')

    context = {
        'correspondance': correspondance,
        'other_user': other_user,
        'chat_messages': msgs,
        'form': form,
    }
    return render(request, 'voyages/conversation.html', context)
