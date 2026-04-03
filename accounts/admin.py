from django.contrib import admin

from .models import CashierInvitation, EmailOTP, Shop, UserProfile


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'phone', 'email', 'usd_to_cdf_rate', 'vat_percentage')
    fieldsets = (
        (None, {'fields': ('name', 'created_by')}),
        (
            'Informations administratives',
            {'fields': ('address', 'rccm', 'id_nat', 'nif', 'bureau', 'phone', 'email')},
        ),
        (
            'Parametres financiers',
            {'fields': ('usd_to_cdf_rate', 'vat_percentage')},
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop', 'position_title', 'employee_code', 'phone', 'currency')
    list_filter = ('shop', 'currency', 'position_title')
    search_fields = ('user__username', 'user__email', 'employee_code', 'phone', 'position_title')


@admin.register(CashierInvitation)
class CashierInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'created_by', 'used_by', 'is_used', 'expires_at', 'created_at')
    list_filter = ('role', 'is_used', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'created_by__username')


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'account_space', 'purpose', 'attempts', 'created_at', 'expires_at', 'consumed_at')
    list_filter = ('account_space', 'purpose', 'created_at')
    search_fields = ('email', 'user__username', 'user__email')
