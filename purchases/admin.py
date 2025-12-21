# purchases/admin.py

from django.contrib import admin
from .models import Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    fields = ['product', 'quantity', 'purchase_price', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'purchase_date', 'supplier', 'total', 
        'item_count', 'is_received'
    ]
    list_filter = ['is_received', 'purchase_date']
    search_fields = ['id', 'supplier', 'invoice_number']
    readonly_fields = ['purchase_date', 'total', 'item_count']
    list_editable = ['is_received']
    inlines = [PurchaseItemInline]
    
    fieldsets = (
        ('Informations d\'achat', {
            'fields': ('purchase_date', 'supplier', 'invoice_number', 'created_by')
        }),
        ('Montant', {
            'fields': ('total', 'item_count')
        }),
        ('Statut', {
            'fields': ('is_received', 'notes')
        }),
    )


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'product', 'quantity', 'purchase_price', 'subtotal']
    list_filter = ['purchase__purchase_date']
    search_fields = ['product__name', 'purchase__id']
    readonly_fields = ['subtotal']
