from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Promotion, PromotionLog


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    """Interface admin pour la gestion des promotions"""
    
    list_display = (
        'name',
        'discount_display',
        'scope_display',
        'status_badge',
        'dates_display',
        'actions_display'
    )
    
    list_filter = (
        'discount_type',
        'scope',
        'is_active',
        'created_at',
    )
    
    search_fields = (
        'name',
        'description',
        'banner_message'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'status',
        'is_running',
        'is_upcoming',
        'is_expired',
        'preview_badge',
    )
    
    fieldsets = (
        ('📌 Informations générales', {
            'fields': ('name', 'description', 'note_business')
        }),
        ('💰 Réduction', {
            'fields': (
                'discount_type',
                'discount_value',
            ),
            'description': 'Configurez le type et la valeur de la réduction'
        }),
        ('🎯 Portée', {
            'fields': (
                'scope',
                'products',
                'categories'
            ),
            'description': 'Sélectionnez les produits/catégories concernés'
        }),
        ('⏰ Programmation', {
            'fields': (
                'start_date',
                'end_date',
                'is_active',
                'status',
                'is_running',
                'is_upcoming',
                'is_expired',
            )
        }),
        ('👁️ Marketing visuel', {
            'fields': (
                'banner_image',
                'banner_message',
                'display_badge',
                'badge_custom_text',
                'preview_badge',
            ),
            'classes': ('collapse',)
        }),
        ('📊 Métadonnées', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('products', 'categories')
    
    def discount_display(self, obj):
        """Affiche la réduction formatée"""
        symbol = '%' if obj.discount_type == 'percentage' else '€'
        return f"{obj.discount_value}{symbol}"
    discount_display.short_description = "Réduction"
    
    def scope_display(self, obj):
        """Affiche la portée de la promotion"""
        scopes = {
            'all_products': '🌍 Tous les produits',
            'specific_products': '📦 Produits sélectionnés',
            'specific_categories': '📂 Catégories sélectionnées',
        }
        return scopes.get(obj.scope, obj.scope)
    scope_display.short_description = "Portée"
    
    def status_badge(self, obj):
        """Affiche le statut avec couleur"""
        colors = {
            'active': '#2ecc71',      # Vert
            'upcoming': '#3498db',    # Bleu
            'expired': '#95a5a6',     # Gris
            'inactive': '#e74c3c',    # Rouge
        }
        color = colors.get(obj.status, '#95a5a6')
        
        status_text = {
            'active': '🟢 ACTIVE',
            'upcoming': '🟡 PROGRAMMÉE',
            'expired': '⚫ EXPIRÉE',
            'inactive': '🔴 INACTIVE',
        }
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            status_text.get(obj.status, obj.status)
        )
    status_badge.short_description = "Statut"
    
    def dates_display(self, obj):
        """Affiche les dates formatées"""
        start = obj.start_date.strftime('%d/%m %H:%M')
        end = obj.end_date.strftime('%d/%m %H:%M')
        return f"{start} → {end}"
    dates_display.short_description = "Période"
    
    def actions_display(self, obj):
        """Actions rapides"""
        if obj.is_active and not obj.is_running:
            return format_html('⏳ En attente')
        elif obj.is_active and obj.is_running:
            return format_html('✅ En cours')
        elif obj.is_expired:
            return format_html('⏹️ Terminée')
        else:
            return format_html('❌ Désactivée')
    actions_display.short_description = "Actions"
    
    def preview_badge(self, obj):
        """Prévisualise le badge"""
        badge_text = obj.get_badge_text()
        return format_html(
            '<span style="background-color: #E63946; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; display: inline-block;">{}</span>',
            badge_text
        )
    preview_badge.short_description = "Aperçu du badge"
    
    def save_model(self, request, obj, form, change):
        """Enregistrer le utilisateur qui crée/modifie"""
        if not change:
            obj.created_by = request.user
        obj._updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimisez les requêtes"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('products', 'categories', 'logs')


@admin.register(PromotionLog)
class PromotionLogAdmin(admin.ModelAdmin):
    """Interface admin pour les logs de promotions"""
    
    list_display = (
        'promotion',
        'action_badge',
        'timestamp_display',
        'performed_by',
    )
    
    list_filter = (
        'action',
        'timestamp',
        'promotion',
    )
    
    search_fields = (
        'promotion__name',
    )
    
    readonly_fields = (
        'promotion',
        'action',
        'timestamp',
        'performed_by',
        'details_display',
    )
    
    fieldsets = (
        ('Infos', {
            'fields': ('promotion', 'action', 'timestamp', 'performed_by')
        }),
        ('Détails', {
            'fields': ('details_display',)
        }),
    )
    
    def action_badge(self, obj):
        """Affiche l'action avec une couleur"""
        action_colors = {
            'created': '#3498db',      # Bleu
            'updated': '#f39c12',      # Orange
            'activated': '#2ecc71',    # Vert
            'deactivated': '#e74c3c',  # Rouge
            'started': '#27ae60',      # Vert foncé
            'ended': '#7f8c8d',        # Gris
            'deleted': '#c0392b',      # Rouge foncé
        }
        color = action_colors.get(obj.action, '#95a5a6')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = "Action"
    
    def timestamp_display(self, obj):
        """Affiche le timestamp formaté"""
        return obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')
    timestamp_display.short_description = "Date/Heure"
    
    def details_display(self, obj):
        """Affiche les détails JSON formatés"""
        import json
        try:
            formatted = json.dumps(obj.details, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted)
        except:
            return str(obj.details)
    details_display.short_description = "Détails"
    
    def has_add_permission(self, request):
        """Les logs ne peuvent pas être créés manuellement"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Les logs ne doivent pas être supprimés"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les logs ne peuvent pas être modifiés"""
        return False
    
    def get_queryset(self, request):
        """Optimisez les requêtes"""
        qs = super().get_queryset(request)
        return qs.select_related('promotion', 'performed_by')
