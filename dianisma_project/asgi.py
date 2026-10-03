"""
ASGI config for dianisma_project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dianisma_project.settings')
application = get_asgi_application()
