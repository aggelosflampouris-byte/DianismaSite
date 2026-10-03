"""
App configuration for DIANISMA.GR Admin Panel.
"""
from django.apps import AppConfig


class AdminpanelConfig(AppConfig):
    """Configuration class for the adminpanel application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adminpanel'
    verbose_name = 'DIANISMA.GR Διαχείριση'
