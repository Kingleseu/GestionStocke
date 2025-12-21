from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('style-guide/', views.StoreStyleGuideView.as_view(), name='style_guide'),
    path('', views.StoreCatalogView.as_view(), name='catalog'),
    path('cart/', views.StoreCartView.as_view(), name='cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.StoreCheckoutView.as_view(), name='checkout'),
    path('api/sync-cart/', views.sync_cart, name='sync_cart'),

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

    # Category Navigator (Universes)
    path('admin/universes/', views.UniverseListView.as_view(), name='admin_universes'),
    path('admin/universes/<int:pk>/update/', views.UniverseUpdateView.as_view(), name='admin_universe_update'),

    # Collections (Zag Style)
    path('admin/collections/', views.CollectionListView.as_view(), name='admin_collections'),
    path('admin/collections/add/', views.CollectionCreateView.as_view(), name='admin_collection_add'),
    path('admin/collections/<int:pk>/update/', views.CollectionUpdateView.as_view(), name='admin_collection_update'),
    path('admin/collections/<int:pk>/delete/', views.CollectionDeleteView.as_view(), name='admin_collection_delete'),
    path('admin/collections/sync/', views.sync_collections, name='admin_collections_sync'),
]
