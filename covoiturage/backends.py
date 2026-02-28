"""
Backend d'authentification : permet de se connecter avec l'email ou le nom d'utilisateur.
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
