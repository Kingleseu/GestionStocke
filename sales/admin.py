# sales/admin.py

from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'sale_date', 'cashier', 'payment_method', 
        'total', 'item_count', 'is_cancelled'
    ]
    list_filter = ['payment_method', 'is_cancelled', 'sale_date']
    search_fields = ['id', 'cashier__username']
    readonly_fields = ['sale_date', 'total', 'item_count']
    inlines = [SaleItemInline]
    
    fieldsets = (
        ('Informations de vente', {
            'fields': ('sale_date', 'cashier', 'payment_method')
        }),
        ('Montant', {
            'fields': ('total', 'item_count')
        }),
        ('Notes', {
            'fields': ('notes', 'is_cancelled')
        }),
    )


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['sale__sale_date']
    search_fields = ['product__name', 'sale__id']
    readonly_fields = ['subtotal']
