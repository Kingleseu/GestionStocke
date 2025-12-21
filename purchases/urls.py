# purchases/urls.py
from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    # Liste des achats
    path('', views.PurchaseListView.as_view(), name='purchase_list'),
    
    # Créer un achat
    path('new/', views.purchase_create_view, name='purchase_create'),
    
    # Détails d'un achat
    path('<int:pk>/', views.PurchaseDetailView.as_view(), name='purchase_detail'),
    
    # Marquer comme reçu/non reçu
    path('<int:pk>/toggle-received/', views.purchase_toggle_received, name='purchase_toggle_received'),
    
    # Historique des achats (décommentez après avoir ajouté la fonction dans views.py)
    # path('history/', views.purchase_history_view, name='purchase_history'),
]