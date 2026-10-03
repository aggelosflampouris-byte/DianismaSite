"""
Custom template filters for article content cleanup.
"""
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='clean_content', is_safe=True)
def clean_content(value):
    """
    Clean article body HTML:
    - Remove literal \\r (backslash + r) followed by real newlines — the exact
      pattern produced during the pgdump import.
    - Remove standalone \\r\\n / \\n escape-looking text sequences.
    - Ensure images are contained and wrapped in figure elements.
    """
    if not value:
        return ''

    content = str(value)

    # Pattern 1: literal backslash-r followed by real newline char (most common from import)
    # repr shows as \\r\n
    content = content.replace('\\\r\n', ' ')
    content = content.replace('\\\n', ' ')
    content = content.replace('\\\r', ' ')

    # Pattern 2: double-escaped \\r\\n (shows as literal text \r\n on page)
    content = content.replace('\\r\\n', ' ')
    content = content.replace('\\r', ' ')
    content = content.replace('\\n', ' ')

    # Clean up multiple whitespace runs
    content = re.sub(r'[ \t]{3,}', ' ', content)

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


@register.filter(name='fix_image_url')
def fix_image_url(url):
    """Fix Cloudinary double image/upload paths."""
    if not url:
        return url
    return url.replace('image/upload/image/upload/', 'image/upload/')
