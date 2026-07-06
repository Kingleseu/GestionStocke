# pembeny/urls.py - PEMBENY B2B Platform

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # PEMBENY B2B Platform URLs
    path('accounts/', include('accounts.urls')),  # Authentification OTP
    path('products/', include('products.urls')),  # Produits et catégories
    path('purchases/', include('purchases.urls')),  # Achats / réapprovisionnement
    path('inventory/', include('inventory.urls')),  # Gestion de stock
    path('reports/', include('reports.urls')),  # Rapports
    path('supply/', include('supply.urls')),  # ⭐ PEMBENY B2B (coeur de l'app)
    path('promotions/', include('promotions.urls')),  # Promotions B2B
    
    # Page d'accueil PEMBENY
    path('', RedirectView.as_view(pattern_name='supply:home', permanent=False)),
]

# Servir les fichiers media en développement
if settings.DEBUG or getattr(settings, 'SERVE_MEDIA_LOCALLY', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)