# redpos/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URLs des applications
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('purchases/', include('purchases.urls')),
    path('inventory/', include('inventory.urls')),
    path('reports/', include('reports.urls')),
    path('store/', include('store.urls')),  # E-commerce
    
    # Page d'accueil - Écran de caisse
    path('', include('sales.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)