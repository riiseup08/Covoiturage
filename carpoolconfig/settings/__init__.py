"""
Django settings for carpoolconfig project.
Auto-selects settings based on DJANGO_ENV environment variable.
"""

import os

ENV = os.environ.get("DJANGO_ENV", "development")

if ENV == "production":
    from carpoolconfig.settings.production import *
else:
    from carpoolconfig.settings.development import *
