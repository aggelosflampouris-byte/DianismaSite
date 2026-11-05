import os
from typing import Optional
from django.conf import settings
from cloudinary_storage.storage import MediaCloudinaryStorage


def get_cloudinary_cloud_name() -> str:
    """Return configured Cloudinary cloud name, defaulting to dh7aqmruq."""
    return getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME') or 'dh7aqmruq'


def normalize_media_url(url: Optional[str]) -> str:
    """
    Standardize Cloudinary and external media URLs:
    - Normalizes legacy/incorrect cloud name ('dianisma') to active cloud name.
    - Strips duplicated 'image/upload/image/upload/' sequences.
    - Upgrades insecure HTTP Cloudinary links to HTTPS.
    - Rejects invalid relative paths (e.g. legacy 'images/default_...jpg') that cause 404s.
    """
    if not url:
        return ''
    cleaned = str(url).strip()
    if not cleaned:
        return ''

    # Reject relative paths that do not start with http(s):// or /
    if not (cleaned.startswith('http://') or cleaned.startswith('https://') or cleaned.startswith('/')):
        return ''

    cloud_name = get_cloudinary_cloud_name()
    if 'res.cloudinary.com/dianisma/' in cleaned:
        cleaned = cleaned.replace('res.cloudinary.com/dianisma/', f'res.cloudinary.com/{cloud_name}/')
    if 'image/upload/image/upload/' in cleaned:
        cleaned = cleaned.replace('image/upload/image/upload/', 'image/upload/')
    if cleaned.startswith('http://res.cloudinary.com/'):
        cleaned = 'https://' + cleaned[len('http://'):]

    return cleaned


class SmartMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Intelligent Cloudinary storage handler.
    Assigns resource_type='raw' for non-image assets (PDFs, DOCX, etc.) and
    defaults to resource_type='image' for all images and extensionless Cloudinary public_ids.
    """
    RAW_EXTENSIONS = ('.pdf', '.docx', '.doc', '.zip', '.txt')

    def _get_resource_type(self, name: str) -> str:
        name_str = str(name or '').lower()
        ext = os.path.splitext(name_str)[1]
        if ext in self.RAW_EXTENSIONS or 'articles/pdfs/' in name_str:
            return 'raw'
        return 'image'


