"""
Backends d'authentification :
1. EmailOrUsernameBackend : connexion avec email ou nom d'utilisateur + mot de passe
2. PhoneOTPBackend : connexion avec numéro de téléphone + code OTP (sans mot de passe)
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Authentifie avec username OU email (si la chaîne contient @)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        username = username.strip()
        if "@" in username:
            user = User.objects.filter(email__iexact=username).first()
        else:
            user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            return user
        return None


class PhoneOTPBackend(ModelBackend):
    """Authentifie avec numéro de téléphone + code OTP (pas de mot de passe)."""

    def authenticate(self, request, phone=None, otp_code=None, **kwargs):
        if phone is None or otp_code is None:
            return None
        from .models import PhoneOTP, Profile
        from .sms import normalize_phone

        phone = normalize_phone(phone)
        if not PhoneOTP.verify(phone, otp_code):
            return None

        # Find user by phone number in profile
        profile = Profile.objects.filter(phone=phone).select_related('user').first()
        if profile:
            # Mark phone as verified on successful OTP login
            if not profile.phone_verified:
                profile.phone_verified = True
                profile.save(update_fields=['phone_verified'])
            return profile.user
        return None
