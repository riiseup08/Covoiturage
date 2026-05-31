"""Mobile-friendly auth endpoints.

The mobile client expects a single login/register call that returns an auth token
plus the user's profile (see mobile/src/context/AuthContext.js). We mint a JWT
under the hood (SimpleJWT) and return its access token as ``token`` — the client
sends it back as ``Authorization: Bearer <token>``.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from covoiturage.services.referrals import apply_referral, ReferralError
from .serializers import ProfileSerializer


def _auth_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        "token": str(refresh.access_token),
        "refresh": str(refresh),
        "user_id": user.id,
        "username": user.username,
        "profile": ProfileSerializer(user.profile).data,
    }


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"error": "Identifiants invalides."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(_auth_payload(user))


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        if not username or not password:
            return Response(
                {"error": "Nom d'utilisateur et mot de passe requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Ce nom d'utilisateur est déjà pris."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if email and User.objects.filter(email=email).exists():
            return Response(
                {"error": "Un compte existe déjà avec cette adresse email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(username=username, email=email, password=password)

        code = (request.data.get("referral_code") or "").strip()
        if code:
            try:
                apply_referral(user, code)
            except ReferralError:
                pass  # invalid code must not block signup

        return Response(_auth_payload(user), status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Stateless JWT: the client discards the token. (Blacklisting would require
        # the token_blacklist app.) Respond 204 so the client can clear its session.
        return Response(status=status.HTTP_204_NO_CONTENT)
