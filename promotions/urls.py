from django.urls import path
from .views import (
    PromotionListView,
    PromotionCreateView,
    PromotionUpdateView,
    PromotionDetailView,
    PromotionDeleteView,
    update_all_promotions,
    promotion_logs_view,
)

app_name = 'promotions'

urlpatterns = [
    # Liste des promotions
    path('', PromotionListView.as_view(), name='promotion_list'),
    
    # Créer une promotion
    path('new/', PromotionCreateView.as_view(), name='promotion_create'),
    
    # Détails d'une promotion
    path('<int:pk>/', PromotionDetailView.as_view(), name='promotion_detail'),
    
    # Modifier une promotion
    path('<int:pk>/edit/', PromotionUpdateView.as_view(), name='promotion_update'),
    
    # Supprimer une promotion
    path('<int:pk>/delete/', PromotionDeleteView.as_view(), name='promotion_delete'),
    
    # Logs d'une promotion
    path('<int:pk>/logs/', promotion_logs_view, name='promotion_logs'),
    
    # Mettre à jour tous les status
    path('update-status/', update_all_promotions, name='update_status'),
]
