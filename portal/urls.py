"""
URL patterns for DIANISMA.GR public portal.
"""
from django.urls import path
from . import views

from django.contrib.sitemaps.views import sitemap
from .sitemaps import ArticleSitemap, CategorySitemap, StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'articles': ArticleSitemap,
}

urlpatterns = [
    path('', views.index, name='index'),
    path('politiki/', views.politiki, name='politiki'),
    path('oikonomia/', views.oikonomia, name='oikonomia'),
    path('koinonia/', views.koinonia, name='koinonia'),
    path('analyseis/', views.analyseis, name='analyseis'),
    path('apopseis/', views.apopseis, name='apopseis'),
    path('dialogues/', views.apopseis, name='dialogues'),
    path('apply-writer/', views.apply_writer, name='apply_writer'),
    path('dialogues/apply/', views.apply_writer, name='dialogues_apply'),
    path('writer-dashboard/', views.writer_dashboard, name='writer_dashboard'),
    path('search/', views.search, name='search'),
    path('article/<str:slug>/', views.article_detail, name='article_detail'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('copyright/', views.copyright_notice, name='copyright_notice'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('api/articles/load-more/', views.load_more_articles, name='load_more_articles'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('category/<slug:slug>/', views.category_generic, name='category'),

    # Legacy SEO redirects (preserve Google backlinks from old site)
    path('tag/<path:tag_name>/', views.legacy_tag_redirect, name='legacy_tag_redirect'),
    path('tag/<path:tag_name>', views.legacy_tag_redirect, name='legacy_tag_redirect_noslash'),
    path('tags/<path:tag_name>/', views.legacy_tag_redirect, name='legacy_tags_redirect'),
    path('tags/<path:tag_name>', views.legacy_tag_redirect, name='legacy_tags_redirect_noslash'),
]
