# inventory/urls.py
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Liste du stock
    path('', views.StockListView.as_view(), name='stock_list'),
    
    # Le Cerveau
    path('brain/', views.brain_dashboard_view, name='brain'),
    
    # API Historique Produit
    path('api/history/<int:product_id>/', views.get_product_history_api, name='api_history'),
]
