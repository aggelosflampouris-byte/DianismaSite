"""
Django settings for DIANISMA.GR news portal project.
"""
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import os

# Load .env file for local development (requires python-dotenv, ignored silently if absent).
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

_secret_key = os.environ.get('DJANGO_SECRET_KEY')
if not _secret_key:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )
SECRET_KEY = _secret_key

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

_allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()] if _allowed_hosts else (['localhost', '127.0.0.1'] if DEBUG else [])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    # Third-party
    'cloudinary',
    'cloudinary_storage',
    # Project Apps
    'adminpanel.apps.AdminpanelConfig',
    'portal.apps.PortalConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise: must be immediately after SecurityMiddleware.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dianisma_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'portal.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'dianisma_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'defaultdb'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'OPTIONS': {
            'ssl': {'ssl_mode': 'REQUIRED'},
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'el'
TIME_ZONE = 'Europe/Athens'
USE_I18N = True
USE_TZ = True

# â”€â”€ Static files (CSS, JS) served by WhiteNoise â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── Cloudinary (media / uploaded images) ──────────────────────────────────────
_cloudinary_url = os.environ.get('CLOUDINARY_URL', '').strip()
_cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', '').strip()
_api_key = os.environ.get('CLOUDINARY_API_KEY', '').strip()
_api_secret = os.environ.get('CLOUDINARY_API_SECRET', '').strip()

# Always enforce active cloud name if empty or legacy 'dianisma'
if not _cloud_name or _cloud_name == 'dianisma':
    _cloud_name = 'dh7aqmruq'

# Support parsing from CLOUDINARY_URL if separate credentials not passed
if _cloudinary_url and (not _api_key or not _api_secret):
    import urllib.parse
    try:
        parsed_c = urllib.parse.urlsplit(_cloudinary_url)
        if parsed_c.scheme == 'cloudinary':
            _api_key = parsed_c.username or _api_key
            _api_secret = parsed_c.password or _api_secret
            if parsed_c.hostname and parsed_c.hostname != 'dianisma':
                _cloud_name = parsed_c.hostname
    except Exception:
        pass

if not _api_key:
    _api_key = '783348361251748'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': _cloud_name,
    'API_KEY':    _api_key,
    'API_SECRET': _api_secret,
}

_has_cloudinary = bool(_api_key and _api_secret) or bool(_cloudinary_url)

STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'dianisma_project.storage.SmartMediaCloudinaryStorage' if _has_cloudinary else 'django.core.files.storage.FileSystemStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/adminpanel/login/'
LOGIN_REDIRECT_URL = '/dialogues/'
LOGOUT_REDIRECT_URL = '/'
