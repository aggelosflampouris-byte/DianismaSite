"""
App configuration for DIANISMA.GR public portal.
"""
from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portal'
    verbose_name = 'DIANISMA.GR Portal'
