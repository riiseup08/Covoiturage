from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
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
from .serializers import (
    VoyageSerializer,
    VoyageCreateSerializer,
    DemandeSerializer,
    CorrespondanceSerializer,
    AvisSerializer,
    ProfileSerializer,
    PublicProfileSerializer,
    NotificationSerializer,
    MessageSerializer,
    SearchQuerySerializer,
    UserSerializer,
    RouteAlertSerializer,
    RecurringTripSerializer,
)
from .permissions import IsOwnerOrReadOnly


class VoyageViewSet(viewsets.ModelViewSet):
    """API endpoint for voyages (trips)."""

    queryset = Voyage.objects.select_related("conducteur", "conducteur__profile")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ville_depart", "ville_arrivee", "modele_voiture"]
    ordering_fields = ["date_depart", "prix_par_place", "created_at"]
    ordering = ["-date_depart"]

    def get_serializer_class(self):
        if self.action == "create":
            return VoyageCreateSerializer
        return VoyageSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "search"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def _is_female(self):
        return bool(
            getattr(getattr(self.request.user, "profile", None), "is_female", False)
            if self.request.user.is_authenticated
            else False
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.filter(
                date_depart__gte=timezone.now(),
                places_disponibles__gte=1,
                est_termine=False,
            )
            # Women-only trips are visible only to female users.
            if not self._is_female():
                queryset = queryset.exclude(women_only=True)
            if self.request.user.is_authenticated:
                queryset = queryset.exclude(conducteur=self.request.user)
            return queryset
        return queryset

    def perform_create(self, serializer):
        from covoiturage.services import trips

        serializer.instance = trips.publish_voyage(
            self.request.user, **serializer.validated_data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search voyages with filters (delegates to the shared service)."""
        from covoiturage.services import trips

        user = request.user if request.user.is_authenticated else None
        queryset = trips.search_voyages(request.query_params, user=user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VoyageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = VoyageSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def mine(self, request):
        """The current user's own published trips (most recent first)."""
        qs = (
            Voyage.objects.filter(conducteur=request.user)
            .select_related("conducteur", "conducteur__profile")
            .order_by("-date_depart")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(VoyageSerializer(page, many=True).data)
        return Response(VoyageSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def termine(self, request, pk=None):
        """Mark the trip terminated; deducts commission (driver only)."""
        from covoiturage.services import trips

        voyage = self.get_object()
        if voyage.conducteur_id != request.user.id:
            return Response(
                {"error": "Seul le conducteur peut terminer ce trajet."},
                status=status.HTTP_403_FORBIDDEN,
            )
        commission = trips.complete_voyage(request.user, voyage)
        return Response(
            {**VoyageSerializer(voyage).data, "commission": str(commission)}
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def match(self, request, pk=None):
        """Create a match request for a voyage."""
        voyage = self.get_object()
        demande_data = request.data

        demande = Demande.objects.create(
            passager=request.user,
            ville_depart=demande_data.get("ville_depart", voyage.ville_depart),
            ville_arrivee=demande_data.get("ville_arrivee", voyage.ville_arrivee),
            date_voyage=demande_data.get("date_voyage", timezone.now().date()),
            places=demande_data.get("places", 1),
        )

        from covoiturage.services.matching import compute_match_score

        score = compute_match_score(voyage, demande)

        correspondance = Correspondance.objects.create(
            voyage=voyage,
            demande=demande,
            score_match=score,
        )

        serializer = CorrespondanceSerializer(correspondance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DemandeViewSet(viewsets.ModelViewSet):
    """API endpoint for demandes (requests)."""

    serializer_class = DemandeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ville_depart", "ville_arrivee"]
    ordering = ["-date_voyage"]

    def get_queryset(self):
        # A user only ever manages their own requests through this endpoint, so
        # scope every action to the owner — prevents retrieving/editing/deleting
        # another user's demande by id (IDOR). IsOwnerOrReadOnly is belt-and-braces.
        return Demande.objects.filter(passager=self.request.user)

    def perform_create(self, serializer):
        from covoiturage.services import trips

        serializer.instance = trips.publish_demande(
            self.request.user, **serializer.validated_data
        )


class CorrespondanceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for correspondances (matches)."""

    serializer_class = CorrespondanceSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["-id"]

    def get_queryset(self):
        return Correspondance.objects.filter(
            Q(voyage__conducteur=self.request.user)
            | Q(demande__passager=self.request.user)
        ).select_related(
            "voyage",
            "voyage__conducteur",
            "voyage__conducteur__profile",
            "demande",
            "demande__passager",
            "demande__passager__profile",
        )

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        """Validate a match (driver only)."""
        correspondance = self.get_object()
        if correspondance.voyage.conducteur != request.user:
            return Response(
                {"error": "Seul le conducteur peut valider ce match"},
                status=status.HTTP_403_FORBIDDEN,
            )

        correspondance.is_validated = True
        correspondance.save()

        Notification.objects.create(
            user=correspondance.demande.passager,
            notification_type="match_validated",
            title="Match validé!",
            message=f"{request.user.username} a validé votre demande de covoiturage.",
            related_correspondance=correspondance,
        )

        serializer = self.get_serializer(correspondance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def refuse(self, request, pk=None):
        """Refuse a match (driver only)."""
        correspondance = self.get_object()
        if correspondance.voyage.conducteur != request.user:
            return Response(
                {"error": "Seul le conducteur peut refuser ce match"},
                status=status.HTTP_403_FORBIDDEN,
            )

        correspondance.refus_conducteur = True
        correspondance.save()

        Notification.objects.create(
            user=correspondance.demande.passager,
            notification_type="match_refused",
            title="Match refusé",
            message=f"{request.user.username} a refusé votre demande de covoiturage.",
        )

        serializer = self.get_serializer(correspondance)
        return Response(serializer.data)

    # ── Escrow (Mobile Money) ──────────────────────────────────────────
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """Passenger pays the fare into escrow (held until trip completion)."""
        from covoiturage.services import escrow

        correspondance = self.get_object()
        if correspondance.demande.passager != request.user:
            return Response(
                {"error": "Seul le passager peut payer cette course."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            escrow.hold(
                correspondance,
                phone=request.data.get("phone", ""),
                provider=request.data.get("provider", "mtn"),
            )
        except escrow.EscrowError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(correspondance).data)

    @action(detail=True, methods=["post"])
    def confirm_trip(self, request, pk=None):
        """Driver confirms pickup and/or dropoff; releases escrow once both are set."""
        from covoiturage.services import escrow

        correspondance = self.get_object()
        voyage = correspondance.voyage
        if voyage.conducteur != request.user:
            return Response(
                {"error": "Seul le conducteur peut confirmer le trajet."},
                status=status.HTTP_403_FORBIDDEN,
            )
        stage = request.data.get("stage")
        if stage == "pickup":
            voyage.driver_confirmed_pickup = True
            voyage.save(update_fields=["driver_confirmed_pickup"])
        elif stage == "dropoff":
            voyage.driver_confirmed_dropoff = True
            voyage.save(update_fields=["driver_confirmed_dropoff"])
        else:
            return Response(
                {"error": "stage doit être 'pickup' ou 'dropoff'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            voyage.driver_confirmed_pickup
            and voyage.driver_confirmed_dropoff
            and correspondance.payment_status == "held"
        ):
            try:
                escrow.release(correspondance)
            except escrow.EscrowError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(correspondance).data)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """Passenger cancels before pickup; held funds are refunded."""
        from covoiturage.services import escrow

        correspondance = self.get_object()
        if correspondance.demande.passager != request.user:
            return Response(
                {"error": "Seul le passager peut demander un remboursement."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            escrow.refund(correspondance)
        except escrow.EscrowError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(correspondance).data)

    # ── Safety: live-trip-share & SOS ──────────────────────────────────
    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        """SMS the caller's emergency contact a link to follow this trip."""
        from covoiturage.services import safety

        correspondance = self.get_object()  # queryset is participant-scoped
        try:
            phone = safety.share_trip(correspondance, request.user)
        except safety.SafetyError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "shared", "contact": phone})

    @action(detail=True, methods=["post"])
    def sos(self, request, pk=None):
        """Send an urgent SOS to the caller's emergency contact."""
        from covoiturage.services import safety

        correspondance = self.get_object()
        try:
            phone = safety.sos(correspondance, request.user)
        except safety.SafetyError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "sos_sent", "contact": phone})


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for profiles."""

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username"]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PublicProfileSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get", "put", "patch"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update current user's profile."""
        profile = request.user.profile

        if request.method == "GET":
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)

        serializer = ProfileSerializer(profile, data=request.data, partial=(request.method == "PATCH"))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvisViewSet(viewsets.ModelViewSet):
    """API endpoint for reviews."""

    serializer_class = AvisSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["-created_at"]

    def get_queryset(self):
        user_id = self.request.query_params.get("user")
        if user_id:
            return Avis.objects.filter(utilisateur_note_id=user_id)
        return Avis.objects.all()

    def perform_create(self, serializer):
        # Enforce the same participation rules as the web flow: only people who
        # actually shared a completed, validated trip may review each other.
        # Reviews feed trust_score, which gates escrow payouts.
        from covoiturage.services.reviews import can_review

        voyage = serializer.validated_data.get("voyage")
        target = serializer.validated_data.get("utilisateur_note")
        ok, reason = can_review(self.request.user, voyage, target)
        if not ok:
            raise ValidationError(reason)
        serializer.save(auteur=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        self.get_queryset().update(is_read=True)
        return Response({"status": "success"})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """API endpoint for messages."""

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["created_at"]

    def _member_correspondances(self):
        """Correspondances the current user is a party to (driver or passenger)."""
        return Correspondance.objects.filter(
            Q(voyage__conducteur=self.request.user)
            | Q(demande__passager=self.request.user)
        )

    def get_queryset(self):
        # Always restrict to conversations the user belongs to — even the nested
        # /correspondances/<pk>/messages/ route, so messages can't be read by id.
        qs = Message.objects.filter(correspondance__in=self._member_correspondances())
        correspondance_id = self.kwargs.get("pk")
        if correspondance_id:
            qs = qs.filter(correspondance_id=correspondance_id)
        return qs.select_related("sender")

    def perform_create(self, serializer):
        # The correspondance comes from the URL (nested route), not the body.
        correspondance = self._member_correspondances().filter(
            pk=self.kwargs.get("pk")
        ).first()
        if correspondance is None:
            raise PermissionDenied("Vous n'avez pas accès à cette conversation.")
        if not correspondance.is_validated:
            raise PermissionDenied("La conversation n'est disponible qu'après validation du match.")
        serializer.save(sender=self.request.user, correspondance=correspondance)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for users."""

    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username"]


class RouteAlertViewSet(viewsets.ModelViewSet):
    """Owner-scoped CRUD for saved-route alerts."""

    serializer_class = RouteAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RouteAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecurringTripViewSet(viewsets.ModelViewSet):
    """Owner-scoped CRUD for weekly commute templates."""

    serializer_class = RecurringTripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecurringTrip.objects.filter(conducteur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(conducteur=self.request.user)


class DashboardView(APIView):
    """Summary counts for the current user's home screen."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from covoiturage.notifications import get_unread_count

        user = request.user
        return Response(
            {
                "total_voyages": Voyage.objects.filter(conducteur=user).count(),
                "total_demandes": Demande.objects.filter(passager=user).count(),
                "total_correspondances": Correspondance.objects.filter(
                    Q(voyage__conducteur=user) | Q(demande__passager=user),
                    refus_conducteur=False,
                    refus_passager=False,
                ).count(),
                "unread_count": get_unread_count(user),
            }
        )


class WalletView(APIView):
    """Current user's wallet balance and transaction history."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from covoiturage.models import Wallet, Transaction

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        transactions = Transaction.objects.filter(wallet=wallet)[:50]
        return Response(
            {
                "balance": str(wallet.balance),
                "currency": wallet.currency,
                "is_active": wallet.is_active,
                "transactions": [
                    {
                        "amount": str(t.amount),
                        "type": t.transaction_type,
                        "description": t.description,
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in transactions
                ],
            }
        )


class HealthCheckView(APIView):
    """Health check endpoint."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "healthy",
                "timestamp": timezone.now().isoformat(),
            }
        )
