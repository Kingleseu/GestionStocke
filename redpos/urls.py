# redpos/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URLs des applications
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('purchases/', include('purchases.urls')),
    path('inventory/', include('inventory.urls')),
    path('reports/', include('reports.urls')),
    path('store/', include('store.urls')),  # E-commerce
    path('promotions/', include('promotions.urls')),  # Gestion des promotions
    
    # Caisse (POS) - accessible via /pos/
    path('pos/', include('sales.urls')),

    # Page d'accueil - Redirige vers la boutique
    path('', RedirectView.as_view(pattern_name='store:catalog', permanent=False)),
]

# Servir les fichiers media en développement
if settings.DEBUG or getattr(settings, 'SERVE_MEDIA_LOCALLY', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
