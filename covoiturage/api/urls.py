from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .auth_views import LoginView, RegisterView, LogoutView
from .views import (
    VoyageViewSet,
    DemandeViewSet,
    CorrespondanceViewSet,
    ProfileViewSet,
    AvisViewSet,
    NotificationViewSet,
    MessageViewSet,
    UserViewSet,
    RouteAlertViewSet,
    RecurringTripViewSet,
    DashboardView,
    WalletView,
    HealthCheckView,
)

router = DefaultRouter()
router.register(r"voyages", VoyageViewSet, basename="voyage")
router.register(r"demandes", DemandeViewSet, basename="demande")
router.register(r"correspondances", CorrespondanceViewSet, basename="correspondance")
router.register(r"profiles", ProfileViewSet, basename="profile")
router.register(r"avis", AvisViewSet, basename="avis")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"users", UserViewSet, basename="user")
router.register(r"route-alerts", RouteAlertViewSet, basename="route-alert")
router.register(r"recurring-trips", RecurringTripViewSet, basename="recurring-trip")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Mobile-friendly auth (returns token + profile in one call)
    path("auth/login/", LoginView.as_view(), name="auth_login"),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("wallet/", WalletView.as_view(), name="wallet"),
    path("health/", HealthCheckView.as_view(), name="health_check"),
    path(
        "correspondances/<int:pk>/messages/",
        MessageViewSet.as_view({"get": "list", "post": "create"}),
        name="correspondance-messages",
    ),
]
