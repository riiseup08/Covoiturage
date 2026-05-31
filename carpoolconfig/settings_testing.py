"""
Test settings - uses SQLite in-memory for faster tests.
"""

from carpoolconfig.settings import *

# Use faster SQLite for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable caching during tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {}

# Faster email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Test-specific settings
DEBUG = True

# Keep tests hermetic: never make live Nominatim geocoding calls.
GEOCODING_ENABLED = False
