from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Hub,
    HubInventory,
    MerchantAccount,
    OrderTrackingEvent,
    ProcurementOrder,
    ProcurementOrderItem,
    SupplyCategory,
    SupplyHomeFeature,
    SupplyHomepageStat,
    SupplyProcessStep,
    Supplier,
    SupplySiteSettings,
    SupplyProduct,
)


@admin.register(SupplyCategory)
class SupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {}  # Pas de slug


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'supply_category', 'active_products_count', 'phone', 'is_active', 'logo_preview']
    list_filter = ['category', 'supply_category', 'is_active']
    search_fields = ['name', 'contact_name', 'phone']
    list_editable = ['is_active']

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:30px;width:auto;border-radius:4px;">', obj.logo.url)
        return '-'
    logo_preview.short_description = 'Logo'


@admin.register(SupplySiteSettings)
class SupplySiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Marque', {'fields': ('brand_name', 'brand_signature', 'logo', 'contact_phone', 'footer_text')}),
        ('Hero', {'fields': ('hero_badge', 'hero_title', 'hero_subtitle', 'primary_cta_text', 'primary_cta_url', 'secondary_cta_text', 'secondary_cta_url')}),
        ('Logique reseau', {'fields': ('network_title', 'network_subtitle')}),
    )


@admin.register(SupplyHomepageStat)
class SupplyHomepageStatAdmin(admin.ModelAdmin):
    list_display = ['value', 'label', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(SupplyHomeFeature)
class SupplyHomeFeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'badge', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(SupplyProcessStep)
class SupplyProcessStepAdmin(admin.ModelAdmin):
    list_display = ['number', 'title', 'order', 'is_active']
    list_display_links = ['title']
    list_editable = ['number', 'order', 'is_active']


class HubInventoryInline(admin.TabularInline):
    model = HubInventory
    extra = 0
    autocomplete_fields = ['product']
    fields = ['product', 'available_quantity', 'reserved_quantity', 'reorder_threshold', 'stock_badge']
    readonly_fields = ['stock_badge']

    def stock_badge(self, obj):
        if not obj.pk:
            return '-'
        colors = {
            'ok': '#16a34a',
            'low': '#f59e0b',
            'out': '#dc2626',
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:999px;font-size:11px;">{} dispo</span>',
            colors.get(obj.stock_status, '#64748b'),
            obj.sellable_quantity,
        )
    stock_badge.short_description = 'Disponible'


@admin.register(Hub)
class HubAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'commune', 'delivery_fee', 'is_active']
    list_filter = ['is_active', 'commune']
    search_fields = ['name', 'code', 'commune']
    list_editable = ['delivery_fee', 'is_active']
    inlines = [HubInventoryInline]


@admin.register(SupplyProduct)
class SupplyProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'category', 'supply_category', 'unit_label', 'wholesale_price', 'currency', 'is_active', 'is_featured', 'image_preview']
    list_filter = ['category', 'supply_category', 'currency', 'is_active', 'is_featured', 'supplier']
    search_fields = ['name', 'brand', 'sku', 'supplier__name']
    list_editable = ['wholesale_price', 'is_active', 'is_featured']
    autocomplete_fields = ['supplier', 'supply_category']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:30px;width:auto;border-radius:4px;">', obj.image.url)
        return '-'
    image_preview.short_description = 'Image'


@admin.register(HubInventory)
class HubInventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'hub', 'available_quantity', 'reserved_quantity', 'sellable_quantity', 'reorder_threshold', 'stock_status']
    list_filter = ['hub', 'product__category']
    search_fields = ['product__name', 'product__supplier__name', 'hub__name', 'hub__code']
    autocomplete_fields = ['hub', 'product']
    list_editable = ['available_quantity', 'reserved_quantity', 'reorder_threshold']


@admin.register(MerchantAccount)
class MerchantAccountAdmin(admin.ModelAdmin):
    list_display = [
        'shop',
        'owner_full_name',
        'shop_type',
        'business_age',
        'prequalification_label',
        'commune',
        'preferred_hub',
        'is_credit_enabled',
        'credit_limit',
        'credit_used',
        'credit_available',
    ]
    list_filter = ['shop_type', 'business_age', 'is_credit_enabled', 'preferred_hub', 'commune']
    search_fields = ['shop__name', 'owner_full_name', 'contact_phone', 'secondary_phone', 'whatsapp']
    autocomplete_fields = ['preferred_hub']


class ProcurementOrderItemInline(admin.TabularInline):
    model = ProcurementOrderItem
    extra = 0
    autocomplete_fields = ['product', 'supplier']
    readonly_fields = ['line_total']


class OrderTrackingEventInline(admin.TabularInline):
    model = OrderTrackingEvent
    extra = 0
    readonly_fields = ['created_at']


@admin.register(ProcurementOrder)
class ProcurementOrderAdmin(admin.ModelAdmin):
    list_display = ['tracking_reference', 'merchant_name', 'hub', 'status', 'payment_method', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'hub', 'created_at']
    search_fields = ['order_number', 'merchant_name', 'contact_phone', 'commune']
    autocomplete_fields = ['user', 'hub']
    readonly_fields = ['order_number', 'subtotal', 'total_amount', 'created_at', 'updated_at']
    inlines = [ProcurementOrderItemInline, OrderTrackingEventInline]


@admin.register(OrderTrackingEvent)
class OrderTrackingEventAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'label', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number', 'label', 'note']
    autocomplete_fields = ['order', 'created_by']