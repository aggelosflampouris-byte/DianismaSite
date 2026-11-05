import os
from typing import Optional
from django.conf import settings
from cloudinary_storage.storage import RawMediaCloudinaryStorage


def get_cloudinary_cloud_name() -> str:
    """Return configured Cloudinary cloud name, defaulting to dh7aqmruq."""
    return getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME') or 'dh7aqmruq'


def normalize_media_url(url: Optional[str]) -> str:
    """
    Standardize Cloudinary and external media URLs:
    - Normalizes legacy/incorrect cloud name ('dianisma') to active cloud name.
    - Strips duplicated 'image/upload/image/upload/' sequences.
    - Upgrades insecure HTTP Cloudinary links to HTTPS.
    """
    if not url:
        return ''
    cleaned = str(url).strip()
    if not cleaned:
        return ''

    cloud_name = get_cloudinary_cloud_name()
    if 'res.cloudinary.com/dianisma/' in cleaned:
        cleaned = cleaned.replace('res.cloudinary.com/dianisma/', f'res.cloudinary.com/{cloud_name}/')
    if 'image/upload/image/upload/' in cleaned:
        cleaned = cleaned.replace('image/upload/image/upload/', 'image/upload/')
    if cleaned.startswith('http://res.cloudinary.com/'):
        cleaned = 'https://' + cleaned[len('http://'):]

    return cleaned


class SmartMediaCloudinaryStorage(RawMediaCloudinaryStorage):
    """
    Intelligent Cloudinary storage handler.
    Automatically assigns resource_type='image' for image extensions and
    resource_type='raw' for non-image assets (PDFs, DOCX, etc.) so uploads
    do not fail with HTTP 500 / Invalid image file format.
    """
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.bmp', '.ico')

    def _get_resource_type(self, name: str) -> str:
        ext = os.path.splitext(name or '')[1].lower()
        if ext in self.IMAGE_EXTENSIONS:
            return 'image'
        return 'raw'


