from django.contrib import admin
from .models import CustomerProfile, Cart, CartItem, WebOrder, WebOrderItem, StoreSettings

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['delivery_fee',]

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

admin.site.register(CustomerProfile)
admin.site.register(Cart)
admin.site.register(WebOrder)
