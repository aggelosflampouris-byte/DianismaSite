"""
Global context processors for DIANISMA.GR templates.
"""
from adminpanel.models import Category, Article, SiteSetting


def global_context(request):
    """Provide common site-wide data to all templates."""
    try:
        categories = Category.objects.all().order_by('order', 'name')
        recent_breaking = Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by('-published_at')[:5]
    except Exception:
        categories = []
        recent_breaking = []

    site_title = SiteSetting.get_setting('site_title', 'DIANISMA.GR')
    site_tagline = SiteSetting.get_setting('site_slogan', 'Ενημέρωση & Δημόσιος Διάλογος')
    site_description = SiteSetting.get_setting('site_description', 'DIANISMA.GR — Έγκυρη ενημέρωση για την Πολιτική, την Οικονομία, την Κοινωνία και τις Αναλύσεις.')

    social_links = {
        'facebook': SiteSetting.get_setting('social_facebook', 'https://facebook.com'),
        'twitter': SiteSetting.get_setting('social_twitter', 'https://x.com'),
        'instagram': SiteSetting.get_setting('social_instagram', 'https://instagram.com'),
        'youtube': SiteSetting.get_setting('social_youtube', 'https://youtube.com'),
    }

    return {
        'site_title': site_title,
        'site_tagline': site_tagline,
        'site_description': site_description,
        'social_links': social_links,
        'nav_categories': categories,
        'recent_breaking': recent_breaking,
    }
