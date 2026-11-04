"""
Vercel build hook: runs Django's collectstatic so WhiteNoise
can serve compressed static assets in production.
"""
import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dianisma_project.settings')
django.setup()
call_command('collectstatic', '--noinput', '--clear')

