from django.contrib import admin
from .models import Shop, UserProfile, CashierInvitation

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'usd_to_cdf_rate', 'vat_percentage')
    fieldsets = (
        (None, {
            'fields': ('name', 'created_by')
        }),
        ('Informations Administratives', {
            'fields': ('address', 'rccm', 'id_nat', 'nif', 'bureau', 'phone', 'email')
        }),
        ('Paramètres Financiers', {
            'fields': ('usd_to_cdf_rate', 'vat_percentage')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop', 'currency')
    list_filter = ('shop', 'currency')

@admin.register(CashierInvitation)
class CashierInvitationAdmin(admin.ModelAdmin):
    list_display = ('token', 'created_by', 'used_by', 'is_used', 'created_at')
