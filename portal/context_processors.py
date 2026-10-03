"""
Global context processors for DIANISMA.GR templates.
"""
from adminpanel.models import Category, Article


def global_context(request):
    """Provide common site-wide data to all templates."""
    try:
        categories = Category.objects.all().order_by('order', 'name')
        recent_breaking = Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by('-published_at')[:5]
    except Exception:
        categories = []
        recent_breaking = []

    return {
        'site_title': 'DIANISMA.GR',
        'site_tagline': 'Ενημέρωση & Δημόσιος Διάλογος',
        'nav_categories': categories,
        'recent_breaking': recent_breaking,
    }
