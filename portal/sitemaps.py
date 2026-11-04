"""
Sitemaps configuration for DIANISMA.GR for Google search indexing.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from adminpanel.models import Article, Category


class ArticleSitemap(Sitemap):
    protocol = "https"
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by('-published_at')

    def lastmod(self, obj):
        return obj.updated_at or obj.published_at or obj.created_at

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    protocol = "https"
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return [
            'index', 'politiki', 'oikonomia', 'koinonia', 'analyseis', 'apopseis',
            'terms', 'privacy', 'cookie_policy', 'copyright_notice', 'about', 'contact'
        ]

    def location(self, item):
        return reverse(item)
