from django.contrib import admin
from .models import CustomerProfile, Cart, CartItem, WebOrder, WebOrderItem, StoreSettings

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['delivery_fee',]

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(WebOrder)
class WebOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'payment_method', 'delivery_type', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'delivery_type', 'created_at']
    search_fields = ['order_number', 'full_name', 'email', 'phone']
    readonly_fields = ['order_number', 'delivery_confirmation_code', 'created_at', 'updated_at']
    fieldsets = (
        ('Informations de commande', {
            'fields': ['order_number', 'user', 'full_name', 'email', 'phone', 'created_at', 'updated_at']
        }),
        ('Validation et statut', {
            'fields': ['status', 'payment_method']
        }),
        ('Livraison', {
            'fields': ['delivery_type', 'delivery_zone', 'delivery_fee', 'address', 'city']
        }),
        ('Preuves de paiement', {
            'fields': ['delivery_confirmation_code']
        }),
        ('Total', {
            'fields': ['total_amount']
        }),
    )

admin.site.register(CustomerProfile)
admin.site.register(Cart)
admin.site.register(WebOrderItem)
