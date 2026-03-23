"""
REST API views for the Covoiturage mobile application.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Avg, Q
from rest_framework import status, generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Profile, Voyage, Demande, Correspondance,
    Avis, Notification, Message, Payment, PhoneOTP, Wallet, WalletTransaction,
)
from .serializers import (
    ProfileSerializer, ProfileUpdateSerializer, UserRegistrationSerializer,
    VoyageSerializer, VoyageCreateSerializer,
    DemandeSerializer, CorrespondanceSerializer,
    AvisSerializer, NotificationSerializer, MessageSerializer,
    PaymentSerializer, PaymentCreateSerializer,
    WalletSerializer, WalletTransactionSerializer, WalletTopupRequestSerializer,
)
from .views import _geocode_voyage
from .sms import normalize_phone, validate_african_phone, send_otp_sms


# ─── Auth ───────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    profile = ProfileSerializer(user.profile).data
    return Response({'token': token.key, 'user_id': user.id, 'username': user.username, 'profile': profile}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username', '')
    password = request.data.get('password', '')
    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'error': 'Identifiants invalides.'}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    profile = ProfileSerializer(user.profile).data
    return Response({'token': token.key, 'user_id': user.id, 'username': user.username, 'profile': profile})


@api_view(['POST'])
def api_logout(request):
    request.user.auth_token.delete()
    return Response({'detail': 'Déconnecté.'})


# ─── Profile ────────────────────────────────────────────────────

@api_view(['GET'])
def api_my_profile(request):
    profile = ProfileSerializer(request.user.profile).data
    avg = Avis.objects.filter(utilisateur_note=request.user).aggregate(avg=Avg('note'))['avg']
    review_count = Avis.objects.filter(utilisateur_note=request.user).count()
    profile['avg_rating'] = round(avg, 1) if avg else None
    profile['review_count'] = review_count
    return Response(profile)


@api_view(['PATCH'])
def api_update_profile(request):
    serializer = ProfileUpdateSerializer(request.user.profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(ProfileSerializer(request.user.profile).data)


@api_view(['GET'])
def api_public_profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur introuvable.'}, status=404)
    profile = ProfileSerializer(user.profile).data
    avg = Avis.objects.filter(utilisateur_note=user).aggregate(avg=Avg('note'))['avg']
    reviews = AvisSerializer(Avis.objects.filter(utilisateur_note=user).order_by('-created_at')[:20], many=True).data
    profile['avg_rating'] = round(avg, 1) if avg else None
    profile['reviews'] = reviews
    return Response(profile)


# ─── Voyages (Trips) ───────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def api_search_voyages(request):
    qs = Voyage.objects.filter(est_termine=False).select_related('conducteur', 'conducteur__profile').order_by('-date_depart')

    ville_depart = request.query_params.get('ville_depart', '').strip()
    ville_arrivee = request.query_params.get('ville_arrivee', '').strip()
    date = request.query_params.get('date', '').strip()
    women_only = request.query_params.get('women_only', '').strip()

    if ville_depart:
        qs = qs.filter(ville_depart__icontains=ville_depart)
    if ville_arrivee:
        qs = qs.filter(ville_arrivee__icontains=ville_arrivee)
    if date:
        qs = qs.filter(date_depart__date=date)
    if women_only == '1':
        qs = qs.filter(women_only=True)

    serializer = VoyageSerializer(qs[:50], many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_my_voyages(request):
    qs = Voyage.objects.filter(conducteur=request.user).order_by('-date_depart')
    return Response(VoyageSerializer(qs, many=True).data)


@api_view(['POST'])
def api_create_voyage(request):
    serializer = VoyageCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    voyage = serializer.save(conducteur=request.user)
    # Enforce women_only only for female drivers
    is_female = getattr(request.user, 'profile', None) and request.user.profile.gender == 'female'
    if not is_female:
        voyage.women_only = False
    _geocode_voyage(voyage)
    voyage.save()
    return Response(VoyageSerializer(voyage).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
def api_update_voyage(request, voyage_id):
    try:
        voyage = Voyage.objects.get(id=voyage_id, conducteur=request.user)
    except Voyage.DoesNotExist:
        return Response({'error': 'Trajet introuvable.'}, status=404)
    old_depart, old_arrivee = voyage.ville_depart, voyage.ville_arrivee
    serializer = VoyageCreateSerializer(voyage, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    voyage = serializer.save()
    is_female = getattr(request.user, 'profile', None) and request.user.profile.gender == 'female'
    if not is_female:
        voyage.women_only = False
    if voyage.ville_depart != old_depart or voyage.ville_arrivee != old_arrivee:
        _geocode_voyage(voyage)
    voyage.save()
    return Response(VoyageSerializer(voyage).data)


@api_view(['DELETE'])
def api_delete_voyage(request, voyage_id):
    try:
        voyage = Voyage.objects.get(id=voyage_id, conducteur=request.user)
    except Voyage.DoesNotExist:
        return Response({'error': 'Trajet introuvable.'}, status=404)
    voyage.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def api_mark_termine(request, voyage_id):
    try:
        voyage = Voyage.objects.get(id=voyage_id, conducteur=request.user)
    except Voyage.DoesNotExist:
        return Response({'error': 'Trajet introuvable.'}, status=404)
    voyage.est_termine = True
    voyage.save()
    return Response({'detail': 'Trajet marqué comme terminé.'})


# ─── Demandes (Ride Requests) ──────────────────────────────────

@api_view(['GET'])
def api_my_demandes(request):
    qs = Demande.objects.filter(passager=request.user).order_by('-date_voyage')
    return Response(DemandeSerializer(qs, many=True).data)


@api_view(['POST'])
def api_create_demande(request):
    serializer = DemandeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(passager=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def api_delete_demande(request, demande_id):
    try:
        demande = Demande.objects.get(id=demande_id, passager=request.user)
    except Demande.DoesNotExist:
        return Response({'error': 'Demande introuvable.'}, status=404)
    demande.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Correspondances (Matches) ─────────────────────────────────

@api_view(['GET'])
def api_my_matches(request):
    qs = Correspondance.objects.filter(
        Q(voyage__conducteur=request.user) | Q(demande__passager=request.user)
    ).select_related('voyage', 'demande', 'voyage__conducteur', 'demande__passager').order_by('-id')
    return Response(CorrespondanceSerializer(qs, many=True).data)


@api_view(['POST'])
def api_validate_match(request, match_id):
    try:
        c = Correspondance.objects.get(id=match_id, voyage__conducteur=request.user)
    except Correspondance.DoesNotExist:
        return Response({'error': 'Match introuvable.'}, status=404)
    c.is_validated = True
    c.save()
    return Response(CorrespondanceSerializer(c).data)


@api_view(['POST'])
def api_refuse_match(request, match_id):
    try:
        c = Correspondance.objects.get(id=match_id, voyage__conducteur=request.user)
    except Correspondance.DoesNotExist:
        return Response({'error': 'Match introuvable.'}, status=404)
    c.refus_conducteur = True
    c.save()
    return Response(CorrespondanceSerializer(c).data)


# ─── Avis (Reviews) ────────────────────────────────────────────

@api_view(['GET'])
def api_my_reviews(request):
    received = AvisSerializer(Avis.objects.filter(utilisateur_note=request.user).order_by('-created_at'), many=True).data
    given = AvisSerializer(Avis.objects.filter(auteur=request.user).order_by('-created_at'), many=True).data
    return Response({'received': received, 'given': given})


@api_view(['POST'])
def api_create_review(request):
    serializer = AvisSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(auteur=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─── Notifications ──────────────────────────────────────────────

@api_view(['GET'])
def api_notifications(request):
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread_count': unread, 'notifications': NotificationSerializer(qs, many=True).data})


@api_view(['POST'])
def api_mark_notification_read(request, notification_id):
    try:
        n = Notification.objects.get(id=notification_id, user=request.user)
    except Notification.DoesNotExist:
        return Response({'error': 'Notification introuvable.'}, status=404)
    n.is_read = True
    n.save()
    return Response({'detail': 'Marquée comme lue.'})


@api_view(['POST'])
def api_mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'detail': 'Toutes marquées comme lues.'})


# ─── Messaging ──────────────────────────────────────────────────

@api_view(['GET'])
def api_conversation(request, correspondance_id):
    try:
        c = Correspondance.objects.get(
            Q(id=correspondance_id),
            Q(voyage__conducteur=request.user) | Q(demande__passager=request.user)
        )
    except Correspondance.DoesNotExist:
        return Response({'error': 'Conversation introuvable.'}, status=404)
    msgs = MessageSerializer(c.messages.order_by('created_at'), many=True).data
    return Response({'correspondance': CorrespondanceSerializer(c).data, 'messages': msgs})


@api_view(['POST'])
def api_send_message(request, correspondance_id):
    try:
        c = Correspondance.objects.get(
            Q(id=correspondance_id),
            Q(voyage__conducteur=request.user) | Q(demande__passager=request.user)
        )
    except Correspondance.DoesNotExist:
        return Response({'error': 'Conversation introuvable.'}, status=404)
    content = request.data.get('content', '').strip()
    if not content:
        return Response({'error': 'Le message ne peut pas être vide.'}, status=400)
    msg = Message.objects.create(correspondance=c, sender=request.user, content=content)
    return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


# ─── Dashboard stats ────────────────────────────────────────────

@api_view(['GET'])
def api_dashboard(request):
    user = request.user
    my_voyages = Voyage.objects.filter(conducteur=user)
    my_demandes = Demande.objects.filter(passager=user)
    matches = Correspondance.objects.filter(
        Q(voyage__conducteur=user) | Q(demande__passager=user)
    )
    validated_matches = matches.filter(is_validated=True)
    completed_as_driver = my_voyages.filter(est_termine=True).count()
    completed_as_passenger = Correspondance.objects.filter(
        demande__passager=user, is_validated=True, voyage__est_termine=True
    ).count()
    avg_rating = Avis.objects.filter(utilisateur_note=user).aggregate(avg=Avg('note'))['avg']
    review_count = Avis.objects.filter(utilisateur_note=user).count()
    unread_notif = Notification.objects.filter(user=user, is_read=False).count()

    return Response({
        'voyages_count': my_voyages.count(),
        'demandes_count': my_demandes.count(),
        'matches_count': matches.count(),
        'validated_matches_count': validated_matches.count(),
        'completed_as_driver': completed_as_driver,
        'completed_as_passenger': completed_as_passenger,
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
        'review_count': review_count,
        'unread_notifications': unread_notif,
    })


# ─── Phone OTP Authentication ──────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_phone_request_otp(request):
    """Send OTP to a phone number (for login or registration)."""
    phone = request.data.get('phone', '').strip()
    phone = normalize_phone(phone)
    if not phone or not validate_african_phone(phone):
        return Response({'error': 'Numéro de téléphone africain invalide.'}, status=400)
    otp = PhoneOTP.generate(phone)
    send_otp_sms(phone, otp.code)
    return Response({'detail': 'Code OTP envoyé.', 'phone': phone})


@api_view(['POST'])
@permission_classes([AllowAny])
def api_phone_verify_otp(request):
    """Verify OTP and log in (if user exists) or return needs_register."""
    phone = normalize_phone(request.data.get('phone', '').strip())
    code = request.data.get('code', '').strip()
    if not phone or not code:
        return Response({'error': 'Téléphone et code requis.'}, status=400)
    if not PhoneOTP.verify(phone, code):
        return Response({'error': 'Code invalide ou expiré.'}, status=400)
    # Check if user exists with this phone
    profile = Profile.objects.filter(phone=phone).select_related('user').first()
    if profile:
        profile.phone_verified = True
        profile.save(update_fields=['phone_verified'])
        token, _ = Token.objects.get_or_create(user=profile.user)
        return Response({
            'status': 'authenticated',
            'token': token.key,
            'user_id': profile.user.id,
            'username': profile.user.username,
            'profile': ProfileSerializer(profile).data,
        })
    return Response({'status': 'needs_register', 'phone': phone})


@api_view(['POST'])
@permission_classes([AllowAny])
def api_phone_register(request):
    """Register a new user with a verified phone number."""
    phone = normalize_phone(request.data.get('phone', '').strip())
    username = request.data.get('username', '').strip()
    if not phone or not username:
        return Response({'error': 'Téléphone et nom d\'utilisateur requis.'}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Ce nom d\'utilisateur est déjà pris.'}, status=400)
    # Create user without password (phone-auth only)
    user = User.objects.create_user(
        username=username,
        email=request.data.get('email', ''),
        password=None,
    )
    user.set_unusable_password()
    user.save()
    profile = user.profile
    profile.phone = phone
    profile.phone_verified = True
    profile.save(update_fields=['phone', 'phone_verified'])
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
        'profile': ProfileSerializer(profile).data,
    }, status=status.HTTP_201_CREATED)


# ─── Payments (Mobile Money / Cash) ────────────────────────────

@api_view(['POST'])
def api_create_payment(request):
    """Initiate a payment for a validated match."""
    serializer = PaymentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        corr = Correspondance.objects.select_related(
            'voyage', 'voyage__conducteur', 'demande', 'demande__passager'
        ).get(id=data['correspondance_id'], demande__passager=request.user, is_validated=True)
    except Correspondance.DoesNotExist:
        return Response({'error': 'Match validé introuvable.'}, status=404)
    # Prevent duplicate pending payments
    if Payment.objects.filter(correspondance=corr, payer=request.user, status='pending').exists():
        return Response({'error': 'Un paiement est déjà en cours.'}, status=400)
    import secrets
    payment = Payment.objects.create(
        correspondance=corr,
        payer=request.user,
        receiver=corr.voyage.conducteur,
        amount=corr.voyage.prix_par_place * corr.demande.places,
        currency=corr.voyage.currency,
        method=data['method'],
        provider=data.get('provider', ''),
        phone_number=data.get('phone_number', ''),
        transaction_ref=f'COV-{secrets.token_hex(6).upper()}',
    )
    if data['method'] == 'cash':
        payment.status = 'completed'
        payment.save(update_fields=['status'])
    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def api_my_payments(request):
    """List payments made or received by the current user."""
    made = Payment.objects.filter(payer=request.user).select_related('receiver', 'correspondance')
    received = Payment.objects.filter(receiver=request.user).select_related('payer', 'correspondance')
    return Response({
        'payments_made': PaymentSerializer(made, many=True).data,
        'payments_received': PaymentSerializer(received, many=True).data,
    })


@api_view(['POST'])
def api_confirm_payment(request, payment_id):
    """Driver confirms receipt of cash payment."""
    try:
        payment = Payment.objects.get(id=payment_id, receiver=request.user, status='pending')
    except Payment.DoesNotExist:
        return Response({'error': 'Paiement introuvable.'}, status=404)
    payment.status = 'completed'
    payment.save(update_fields=['status'])
    
    # Auto-deduct commission for cash payments from driver wallet
    if payment.method == 'cash':
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if payment.calculate_commission() > 0:
            wallet.balance -= payment.commission_amount
            wallet.save(update_fields=['balance', 'updated_at'])
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='commission_deducted',
                amount=payment.commission_amount,
                currency=payment.currency,
                description=f"Commission prélevée - Trajet {payment.correspondance.voyage.id}",
                related_payment=payment,
            )
    
    return Response(PaymentSerializer(payment).data)


# ─── Wallet (Driver Commission System) ─────────────────────────

@api_view(['GET'])
def api_wallet_balance(request):
    """Get driver's wallet balance and status."""
    if not request.user.profile.is_driver:
        return Response({'error': 'Vous devez être chauffeur.'}, status=403)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    return Response(WalletSerializer(wallet).data)


@api_view(['POST'])
def api_request_topup(request):
    """Request wallet top-up via Mobile Money."""
    if not request.user.profile.is_driver:
        return Response({'error': 'Vous devez être chauffeur.'}, status=403)
    
    serializer = WalletTopupRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    
    # Create placeholder Payment record for top-up tracking
    payment = Payment.objects.create(
        payer=request.user,
        receiver=request.user,  # Self-payment for wallet top-up
        amount=data['amount'],
        currency='XAF',
        method='mobile_money',
        provider=data['provider'],
        phone_number=data['phone_number'],
        transaction_ref=f'TOPUP-{secrets.token_hex(6).upper()}',
        correspondance_id=None,  # No trip associated
    )
    
    # In production, integrate with payment provider API here
    # For now, return pending status
    return Response({
        'status': 'pending',
        'transaction_ref': payment.transaction_ref,
        'amount': payment.amount,
        'currency': payment.currency,
        'provider': payment.provider,
        'message': f'Envoyez {data["amount"]} XAF à {data["phone_number"]} via {data["provider"]}'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def api_confirm_topup(request, payment_id):
    """Confirm wallet top-up (called by payment webhook or user confirmation)."""
    try:
        payment = Payment.objects.get(id=payment_id, payer=request.user, status='pending')
    except Payment.DoesNotExist:
        return Response({'error': 'Paiement introuvable.'}, status=404)
    
    # Mark payment as completed
    payment.status = 'completed'
    payment.save(update_fields=['status'])
    
    # Add funds to wallet
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.balance += payment.amount
    wallet.save(update_fields=['balance', 'updated_at'])
    
    # Record as wallet transaction
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='topup',
        amount=payment.amount,
        currency=payment.currency,
        description=f"Recharge via {payment.get_provider_display()}",
        related_payment=payment,
    )
    
    return Response({
        'status': 'completed',
        'wallet_balance': str(wallet.balance),
        'message': 'Recharge réussie!'
    })


@api_view(['GET'])
def api_wallet_transactions(request):
    """Get wallet transaction history."""
    if not request.user.profile.is_driver:
        return Response({'error': 'Vous devez être chauffeur.'}, status=403)
    
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()[:50]  # Last 50 transactions
    return Response(WalletTransactionSerializer(transactions, many=True).data)
