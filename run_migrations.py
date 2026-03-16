#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpoolconfig.settings')
django.setup()

from django.core.management import call_command

# Make migrations with auto option
call_command('makemigrations', interactive=False)
call_command('migrate')

print("Migrations completed successfully!")
