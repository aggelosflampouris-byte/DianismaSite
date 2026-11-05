"""
Custom template filters for article content cleanup.
"""
import re
from django import template
from django.utils.safestring import mark_safe
from dianisma_project.storage import get_cloudinary_cloud_name

register = template.Library()


@register.filter(name='clean_content', is_safe=True)
def clean_content(value, featured_image_url=None):
    """
    Clean article body HTML:
    - Remove literal \\r (backslash + r) followed by real newlines — the exact
      pattern produced during the pgdump import.
    - Remove standalone \\r\\n / \\n escape-looking text sequences.
    - Remove duplicate occurrences of the featured image from the body.
    - Remove inline base64 images that may leak from office documents.
    - Ensure remaining legitimate content images are contained and wrapped in figure elements.
    - Correct legacy Cloudinary cloud name.
    """
    if not value:
        return ''

    content = str(value)

    # Fix legacy Cloudinary cloud name in body images dynamically
    cloud_name = get_cloudinary_cloud_name()
    content = content.replace('res.cloudinary.com/dianisma/', f'res.cloudinary.com/{cloud_name}/')

    # Pattern 1: literal backslash-r followed by real newline char (most common from import)
    content = content.replace('\\\r\n', ' ')
    content = content.replace('\\\n', ' ')
    content = content.replace('\\\r', ' ')

    # Pattern 2: double-escaped \\r\\n (shows as literal text \r\n on page)
    content = content.replace('\\r\\n', ' ')
    content = content.replace('\\r', ' ')
    content = content.replace('\\n', ' ')

    # Clean up multiple whitespace runs
    content = re.sub(r'[ \t]{3,}', ' ', content)

    # Strip out base64 data URIs or raw duplicate embedded images that might have slipped into content body
    content = re.sub(r'<img[^>]+src=["\']data:image/[^"\']+["\'][^>]*>', '', content, flags=re.IGNORECASE)

    # If a featured image URL is known, strip any <img> tag inside the body that references it
    if featured_image_url and str(featured_image_url).strip():
        f_url = str(featured_image_url).strip()
        # Escape for regex safely
        f_pattern = re.escape(f_url)
        content = re.sub(rf'<figure[^>]*>\s*<img[^>]+src=["\']{f_pattern}["\'][^>]*>\s*(<figcaption[^>]*>.*?</figcaption>\s*)?</figure>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(rf'<img[^>]+src=["\']{f_pattern}["\'][^>]*>', '', content, flags=re.IGNORECASE)

    # Wrap bare <img> tags in figure for better styling control
    content = re.sub(
        r'(<img\b(?![^>]*class="article-figure-img")[^>]*>)',
        r'<figure class="article-figure">\1</figure>',
        content,
        flags=re.IGNORECASE
    )

    # Remove doubled figure wrappers (in case content already had them)
    content = re.sub(
        r'<figure class="article-figure">(<figure[^>]*>)',
        r'\1',
        content
    )

    return mark_safe(content)

