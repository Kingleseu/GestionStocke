# products/admin.py

from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'barcode', 'category', 'selling_price', 
        'current_stock', 'stock_status', 'is_active'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'barcode']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'profit_margin', 'stock_status']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'barcode', 'category', 'description', 'image')
        }),
        ('Prix', {
            'fields': ('purchase_price', 'selling_price', 'profit_margin')
        }),
        ('Stock', {
            'fields': ('current_stock', 'minimum_stock', 'stock_status')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
