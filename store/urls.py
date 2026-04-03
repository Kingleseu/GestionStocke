from django.urls import path
from . import views
from products.views import get_product_customization_data_public

app_name = 'store'

urlpatterns = [
    path('style-guide/', views.StoreStyleGuideView.as_view(), name='style_guide'),
    path('', views.StoreCatalogView.as_view(), name='catalog'),
    path('cart/', views.StoreCartView.as_view(), name='cart'),
    path('product/<int:pk>/', views.StoreProductDetailView.as_view(), name='product_detail'),
    path('studio/<int:pk>/', views.StoreStudioView.as_view(), name='studio'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.StoreCheckoutView.as_view(), name='checkout'),
    path('payment-instructions/<int:order_id>/', views.ManualPaymentInstructionsView.as_view(), name='payment_instructions'),
    path('payment-submit/<int:order_id>/', views.ManualPaymentSubmissionView.as_view(), name='payment_submit'),
    path('account/profile/', views.StoreCustomerProfileView.as_view(), name='account_profile'),
    path('account/orders/', views.CustomerOrderListView.as_view(), name='account_orders'),
    path('account/orders/<str:order_number>/', views.CustomerOrderDetailView.as_view(), name='account_order_detail'),
    path('account/orders/<str:order_number>/invoice/', views.CustomerOrderInvoiceView.as_view(), name='account_order_invoice'),
    path('api/sync-cart/', views.sync_cart, name='sync_cart'),
    
    # API endpoints
    path('api/product/<int:product_id>/customization-data/', get_product_customization_data_public, name='get_customization_data'),

    # Administration Site Web
    path('admin/', views.WebsiteDashboardView.as_view(), name='admin_dashboard'),
    path('admin/hero/update/', views.HeroSectionUpdateView.as_view(), name='admin_hero_update'),
    
    path('admin/hero-cards/', views.HeroCardListView.as_view(), name='admin_hero_cards'),
    path('admin/hero-cards/add/', views.HeroCardCreateView.as_view(), name='admin_hero_card_add'),
    path('admin/hero-cards/<int:pk>/update/', views.HeroCardUpdateView.as_view(), name='admin_hero_card_update'),
    path('admin/hero-cards/<int:pk>/delete/', views.HeroCardDeleteView.as_view(), name='admin_hero_card_delete'),

    path('admin/about/update/', views.AboutSectionUpdateView.as_view(), name='admin_about_update'),
    
    path('admin/stats/', views.AboutStatListView.as_view(), name='admin_about_stats'),
    path('admin/stats/add/', views.AboutStatCreateView.as_view(), name='admin_about_stat_add'),
    path('admin/stats/<int:pk>/update/', views.AboutStatUpdateView.as_view(), name='admin_about_stat_update'),
    path('admin/stats/<int:pk>/delete/', views.AboutStatDeleteView.as_view(), name='admin_about_stat_delete'),

    # Footer Configuration
    path('admin/footer/config/', views.FooterConfigUpdateView.as_view(), name='admin_footer_config'),

    # Social Links
    path('admin/social/', views.SocialLinkListView.as_view(), name='admin_social_links'),
    path('admin/social/add/', views.SocialLinkCreateView.as_view(), name='admin_social_link_add'),
    path('admin/social/<int:pk>/update/', views.SocialLinkUpdateView.as_view(), name='admin_social_link_update'),
    path('admin/social/<int:pk>/delete/', views.SocialLinkDeleteView.as_view(), name='admin_social_link_delete'),

    # Footer Links
    path('admin/footer-links/', views.FooterLinkListView.as_view(), name='admin_footer_links'),
    path('admin/footer-links/add/', views.FooterLinkCreateView.as_view(), name='admin_footer_link_add'),
    path('admin/footer-links/<int:pk>/update/', views.FooterLinkUpdateView.as_view(), name='admin_footer_link_update'),
    path('admin/footer-links/<int:pk>/delete/', views.FooterLinkDeleteView.as_view(), name='admin_footer_link_delete'),

    # Categories
    path('admin/categories/', views.CategoryListView.as_view(), name='admin_categories'),
    path('admin/categories/add/', views.CategoryCreateView.as_view(), name='admin_category_add'),
    path('admin/categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='admin_category_update'),
    path('admin/categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='admin_category_delete'),

    # Settings
    path('admin/settings/', views.StoreSettingsUpdateView.as_view(), name='admin_settings_update'),
    path('admin/shop/update/', views.ShopUpdateView.as_view(), name='admin_shop_update'),

    # Category Navigator (Universes)
    path('admin/universes/', views.UniverseListView.as_view(), name='admin_universes'),
    path('admin/universes/<int:pk>/update/', views.UniverseUpdateView.as_view(), name='admin_universe_update'),
    path('admin/universes/<int:pk>/delete/', views.UniverseDeleteView.as_view(), name='admin_universe_delete'),
    path('admin/universes/sync/', views.sync_universes, name='admin_universes_sync'),

    # Collections (Zag Style)
    path('admin/collections/', views.CollectionListView.as_view(), name='admin_collections'),
    path('admin/collections/add/', views.CollectionCreateView.as_view(), name='admin_collection_add'),
    path('admin/collections/<int:pk>/update/', views.CollectionUpdateView.as_view(), name='admin_collection_update'),
    path('admin/collections/<int:pk>/delete/', views.CollectionDeleteView.as_view(), name='admin_collection_delete'),
    path('admin/collections/sync/', views.sync_collections, name='admin_collections_sync'),

    # Notifications
    path('admin/notifications/feed/', views.notifications_feed, name='admin_notifications_feed'),
    path('admin/notifications/mark-all-read/', views.mark_all_notifications_read, name='admin_notifications_mark_all_read'),
    path('admin/notifications/<int:pk>/open/', views.open_notification, name='admin_notification_open'),
    
    # Web Orders Management
    path('admin/orders/', views.WebOrderListView.as_view(), name='admin_weborders'),
    path('admin/orders/whatsapp/', views.WebOrderWhatsAppView.as_view(), name='admin_weborders_whatsapp'),
    path('admin/orders/<int:pk>/', views.WebOrderDetailView.as_view(), name='admin_weborder_detail'),
    path('admin/orders/<int:pk>/update-status/', views.update_order_status, name='admin_weborder_update_status'),
    
    # Payments Management
    path('admin/payments/', views.AdminPaymentListView.as_view(), name='admin_payments'),
    path('admin/payments/<int:pk>/approve/', views.approve_payment, name='admin_payment_approve'),
    path('admin/payments/<int:pk>/reject/', views.reject_payment, name='admin_payment_reject'),
    # Delivery Zones
    path('admin/delivery-zones/', views.DeliveryZoneListView.as_view(), name='admin_delivery_zones'),
    path('admin/delivery-zones/add/', views.DeliveryZoneCreateView.as_view(), name='admin_delivery_zone_add'),
    path('admin/delivery-zones/<int:pk>/update/', views.DeliveryZoneUpdateView.as_view(), name='admin_delivery_zone_update'),
    path('admin/delivery-zones/<int:pk>/delete/', views.DeliveryZoneDeleteView.as_view(), name='admin_delivery_zone_delete'),
]

# Add Promotions URLs if the app is available
if hasattr(views, 'PromotionListView'):
    urlpatterns += [
        path('admin/promotions/', views.PromotionListView.as_view(), name='admin_promotions'),
        path('admin/promotions/add/', views.PromotionCreateView.as_view(), name='admin_promotion_add'),
        path('admin/promotions/<int:pk>/update/', views.PromotionUpdateView.as_view(), name='admin_promotion_update'),
        path('admin/promotions/<int:pk>/delete/', views.PromotionDeleteView.as_view(), name='admin_promotion_delete'),
        path('api/products-json/', views.get_products_json, name='api_products_json'),
        path('admin/api/active-promotions/', views.get_active_promotions_api, name='api_active_promotions'),
    ]
