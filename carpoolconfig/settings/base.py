"""
Base settings - common configuration for all environments.
"""

import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")

DEBUG = os.environ.get("DJANGO_DEBUG", "False").strip().lower() in ("true", "1", "yes")
ENV = os.environ.get("DJANGO_ENV", "development")

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
    and (origin.strip().startswith("http://") or origin.strip().startswith("https://"))
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "covoiturage",
    "rest_framework",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "carpoolconfig.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "carpoolconfig.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Douala"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [("fr", "Français"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]

DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATE_FORMAT = "d/m/Y"

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_REDIRECT_URL = "covoiturage:dashboard"
LOGOUT_REDIRECT_URL = "covoiturage:landing"

AUTHENTICATION_BACKENDS = [
    "covoiturage.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]


def _env_int(name, default):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
if EMAIL_BACKEND:
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
    EMAIL_PORT = _env_int("EMAIL_PORT", 587)
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_TIMEOUT = _env_int("EMAIL_TIMEOUT", 10)
else:
    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.dummy.EmailBackend"
    )

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@covoit.africa")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

NOMINATIM_USER_AGENT = os.environ.get("NOMINATIM_USER_AGENT", "covoiturage-geocoder")
NOMINATIM_TIMEOUT = _env_int("NOMINATIM_TIMEOUT", 5)
NOMINATIM_LANGUAGE = os.environ.get("NOMINATIM_LANGUAGE", "fr")
NOMINATIM_MIN_DELAY = _env_int("NOMINATIM_MIN_DELAY", 1)

# Corridor (route-based) matching.
# Distances are measured against the straight-line (great-circle) chord between a
# trip's start and end, so the threshold must absorb how far the real road bends
# away from that chord — towns genuinely "on the way" over a ~200 km inter-city
# route can sit 20-30 km from the chord. Production should swap the straight-line
# test for road routing (e.g. OSRM) and tighten these to a few km.
CORRIDOR_MATCHING_ENABLED = os.environ.get(
    "CORRIDOR_MATCHING_ENABLED", "true"
).strip().lower() in ("1", "true", "yes")
MAX_PICKUP_DETOUR_KM = _env_int("MAX_PICKUP_DETOUR_KM", 30)
MAX_DROPOFF_DETOUR_KM = _env_int("MAX_DROPOFF_DETOUR_KM", 30)

# Mobile-Money escrow provider (default: in-memory stub, no external account)
PAYMENT_PROVIDER = os.environ.get(
    "PAYMENT_PROVIDER", "covoiturage.payments.stub.StubProvider"
)

# USSD / SMS fallback for feature phones
USSD_ENABLED = os.environ.get("USSD_ENABLED", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)
SMS_GATEWAY = os.environ.get(
    "SMS_GATEWAY", "covoiturage.messaging_gateway.console.ConsoleGateway"
)

# Public base URL used to build share / SOS / trip-status links sent over SMS.
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000").rstrip("/")

# Trust & safety: women-only rides (only female drivers may offer them; never
# matched or surfaced to non-female passengers).
WOMEN_ONLY_ENABLED = os.environ.get("WOMEN_ONLY_ENABLED", "true").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Referral bonus (FCFA/XAF) credited to both referrer and referee on the
# referee's first completed trip.
REFERRAL_BONUS_XAF = _env_int("REFERRAL_BONUS_XAF", 500)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "covoit",
        "TIMEOUT": 300,
    }
}

CACHE_TTL = 300

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "search": "30/minute",
    },
    "DATETIME_FORMAT": "%d/%m/%Y %H:%M",
    "DATETIME_INPUT_FORMATS": ["%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M"],
}

SIMPLE_JWT = {
    # SimpleJWT requires timedelta objects, not bare ints. The env vars are in minutes.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=_env_int("JWT_ACCESS_TOKEN_LIFETIME", 60 * 24)),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=_env_int("JWT_REFRESH_TOKEN_LIFETIME", 60 * 24 * 7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
