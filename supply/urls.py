from django.urls import path

from . import views


app_name = 'supply'

urlpatterns = [
    path('', views.SupplyHomeView.as_view(), name='home'),
    path('register/', views.MerchantSignupView.as_view(), name='register'),
    path('dashboard/', views.MerchantDashboardView.as_view(), name='dashboard'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<str:order_number>/', views.ProcurementOrderDetailView.as_view(), name='order_detail'),
    path('api/catalog/', views.catalog_api, name='catalog_api'),
    
    # OPS Dashboard
    path('ops/', views.SupplyOpsDashboardView.as_view(), name='ops_dashboard'),
    path('ops/content/', views.SupplySiteContentView.as_view(), name='ops_site_content'),
    path('ops/content/settings/', views.SupplySiteSettingsUpdateView.as_view(), name='ops_site_settings'),
    path('ops/content/stats/add/', views.HomepageStatCreateView.as_view(), name='ops_stat_add'),
    path('ops/content/stats/<int:pk>/edit/', views.HomepageStatUpdateView.as_view(), name='ops_stat_edit'),
    path('ops/content/features/add/', views.HomeFeatureCreateView.as_view(), name='ops_feature_add'),
    path('ops/content/features/<int:pk>/edit/', views.HomeFeatureUpdateView.as_view(), name='ops_feature_edit'),
    path('ops/content/process/add/', views.ProcessStepCreateView.as_view(), name='ops_process_add'),
    path('ops/content/process/<int:pk>/edit/', views.ProcessStepUpdateView.as_view(), name='ops_process_edit'),
    
    # OPS Categories PEMBENY
    path('ops/categories/', views.CategoryListView.as_view(), name='ops_categories'),
    path('ops/categories/add/', views.CategoryCreateView.as_view(), name='ops_category_add'),
    path('ops/categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='ops_category_edit'),
    
    # OPS Suppliers
    path('ops/suppliers/', views.SupplierListView.as_view(), name='ops_suppliers'),
    path('ops/suppliers/add/', views.SupplierCreateView.as_view(), name='ops_supplier_add'),
    path('ops/suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='ops_supplier_edit'),
    
    # OPS Hubs
    path('ops/hubs/', views.HubListView.as_view(), name='ops_hubs'),
    path('ops/hubs/add/', views.HubCreateView.as_view(), name='ops_hub_add'),
    path('ops/hubs/<int:pk>/edit/', views.HubUpdateView.as_view(), name='ops_hub_edit'),
    
    # OPS Products
    path('ops/products/', views.ProductListView.as_view(), name='ops_products'),
    path('ops/products/add/', views.ProductCreateView.as_view(), name='ops_product_add'),
    path('ops/products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='ops_product_edit'),
    
    # OPS Inventory
    path('ops/inventory/', views.InventoryListView.as_view(), name='ops_inventory'),
    path('ops/inventory/add/', views.InventoryCreateView.as_view(), name='ops_inventory_add'),
    path('ops/inventory/<int:pk>/edit/', views.InventoryUpdateView.as_view(), name='ops_inventory_edit'),
    
    # OPS Orders
    path('ops/orders/', views.OpsOrderListView.as_view(), name='ops_orders'),
    path('ops/orders/<int:pk>/', views.OpsOrderDetailView.as_view(), name='ops_order_detail'),
    path('ops/orders/<int:pk>/status/', views.update_order_status, name='ops_update_order_status'),
    
    # OPS Merchants
    path('ops/merchants/', views.MerchantAccountListView.as_view(), name='ops_merchants'),
    path('ops/merchants/<int:pk>/', views.MerchantAccountDetailView.as_view(), name='ops_merchant_detail'),
    path('ops/merchants/<int:pk>/edit/', views.MerchantAccountUpdateView.as_view(), name='ops_merchant_edit'),
    
    # OPS Utilities
    path('ops/toggle/<str:model_name>/<int:pk>/', views.toggle_active, name='ops_toggle_active'),
]