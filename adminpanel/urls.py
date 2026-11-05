"""
URL configuration for DIANISMA.GR Boss Admin Dashboard (/adminpanel/).
"""
from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('api/dashboard/traffic/', views.api_dashboard_traffic, name='api_dashboard_traffic'),

    # Articles
    path('articles/', views.articles_list, name='articles_list'),
    path('articles/create/', views.article_create, name='article_create'),
    path('articles/parse-document/', views.article_parse_document_ajax, name='article_parse_document'),
    path('articles/<int:article_id>/edit/', views.article_edit, name='article_edit'),
    path('articles/<int:article_id>/delete/', views.article_delete, name='article_delete'),
    path('articles/<int:article_id>/toggle-status/', views.article_toggle_status, name='article_toggle_status'),
    path('articles/<int:article_id>/toggle-featured/', views.article_toggle_featured, name='article_toggle_featured'),

    # Users (Boss only)
    path('users/', views.users_list, name='users_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('api/users/<int:user_id>/change-password/', views.api_user_change_password, name='api_user_change_password'),

    # Categories
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:cat_id>/edit/', views.category_edit, name='category_edit'),

    # Settings (Boss only)
    path('settings/', views.site_settings, name='site_settings'),
]
