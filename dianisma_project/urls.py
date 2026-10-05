"""
Central URL configuration for dianisma_project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # Redirect default Django Admin (/admin/) to Custom Admin Dashboard (/adminpanel/).
    # Uses 302 (temporary) to avoid the browser permanently caching this redirect.
    path('admin/', RedirectView.as_view(url='/adminpanel/', permanent=False)),

    # 2. Custom Admin Dashboard
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),

    # 3. Public portal & Dialogues
    path('', include('portal.urls')),
]

handler404 = 'portal.views.custom_404'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
