# products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Liste des produits
    path('', views.ProductListView.as_view(), name='product_list'),
    
    # Créer un produit
    path('new/', views.ProductCreateView.as_view(), name='product_create'),
    
    # Modifier un produit
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    
    # Supprimer (désactiver) un produit
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Activer/désactiver un produit
    path('<int:pk>/toggle/', views.product_toggle_active, name='product_toggle'),
    
    # ============================================
    # CATEGORY URLS
    # ============================================
    
    # Liste des catégories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Créer une catégorie
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    
    # Modifier une catégorie
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # Supprimer une catégorie
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # ============================================
    # BARCODE URLS
    # ============================================
    
    # Image du code-barres
    path('barcode/<str:barcode_number>/image/', views.barcode_image_view, name='barcode_image'),
    
    # Générer un code-barres (AJAX)
    path('barcode/generate/new/', views.generate_barcode_ajax, name='generate_barcode_ajax'),

    # Actions groupées
    path('bulk-action/', views.product_bulk_action, name='product_bulk_action'),
]