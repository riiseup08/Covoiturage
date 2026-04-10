import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "carpoolconfig.settings")
django.setup()

from django.test import Client
from django.test.utils import override_settings

with override_settings(DEBUG=False, ALLOWED_HOSTS=['127.0.0.1']):
    c = Client()
    r = c.get('/accounts/login/')
    print('GET status:', r.status_code)
    r2 = c.post('/accounts/login/', {'username': 'doesnotexist', 'password': 'x'})
    print('POST status:', r2.status_code)
    snippet = r2.content[:800].decode('utf-8', errors='replace')
    print('POST snippet:')
    print(snippet)