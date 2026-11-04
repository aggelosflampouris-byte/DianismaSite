import os
from cloudinary_storage.storage import RawMediaCloudinaryStorage


class SmartMediaCloudinaryStorage(RawMediaCloudinaryStorage):
    """
    Intelligent Cloudinary storage handler.
    Automatically assigns resource_type='image' for image extensions and
    resource_type='raw' for non-image assets (PDFs, DOCX, etc.) so uploads
    do not fail with HTTP 500 / Invalid image file format.
    """
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.bmp', '.ico')

    def _get_resource_type(self, name):
        ext = os.path.splitext(name or '')[1].lower()
        if ext in self.IMAGE_EXTENSIONS:
            return 'image'
        return 'raw'

