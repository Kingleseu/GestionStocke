# sales/urls.py
from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Écran de caisse
    path('', views.pos_view, name='pos'),
    
    # API recherche produits (AJAX)
    path('api/search-products/', views.search_products, name='search_products'),
    
    # Valider une vente
    path('api/validate-sale/', views.validate_sale, name='validate_sale'),
    
    # Ticket de caisse
    path('receipt/<int:sale_id>/', views.receipt_view, name='receipt'),
    
    # Historique des ventes
    path('history/', views.sales_history_view, name='sales_history'),
]
