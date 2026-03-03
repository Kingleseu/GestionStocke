"""
Admin Django pour la gestion des produits personnalisables
Interface no-code inspirée de Canva
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import (
    CustomizationTemplate, Category, Product, CustomizationPreview,
    CustomizationFont, CustomizableComponent, ProductCustomizationConfig
)


@admin.register(CustomizationTemplate)
class CustomizationTemplateAdmin(admin.ModelAdmin):
    """
    Admin pour les templates de personnalisation.
    Interface simplifiée avec JSONField éditable.
    """
    list_display = ['name', 'is_active', 'products_count', 'preview_rules', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'pretty_rules']
    
    fieldsets = (
        ('📋 Informations', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('⚙️ Règles de Personnalisation', {
            'fields': ('rules', 'pretty_rules'),
            'description': '''
            <div style="background: #f0f8ff; padding: 15px; border-left: 4px solid #2196F3; margin: 10px 0;">
                <h3 style="margin-top:0;">💡 Guide des règles JSON</h3>
                <p><strong>Structure de base :</strong></p>
                <pre style="background: white; padding: 10px; border-radius: 4px;">
{
  "version": "2.0",
  "zones": [
    {
      "id": "unique_id",
      "type": "text|selection|image",
      "label": "Nom affiché",
      "required": true/false,
      "conditions": {"autre_zone_id": "valeur"},
      "constraints": {
        "max_length": 20,
        "allowed_fonts": ["Arial", "Cursive"]
      },
      "price_formula": {
        "base": 5.00,
        "per_char": 0.50
      }
    }
  ]
}
                </pre>
            </div>
            '''
        }),
        ('📅 Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def products_count(self, obj):
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?customization_template__id__exact={obj.id}'
            return format_html('<a href="{}">{} produit(s)</a>', url, count)
        return '0 produit'
    products_count.short_description = '📦 Produits'
    
    def preview_rules(self, obj):
        if obj.rules and obj.rules.get('zones'):
            zones_count = len(obj.rules['zones'])
            return f"✅ {zones_count} zone(s)"
        return "⚠️ Vide"
    preview_rules.short_description = 'Règles'
    
    def pretty_rules(self, obj):
        """Affichage JSON formaté en lecture seule"""
        if obj.rules:
            pretty_json = json.dumps(obj.rules, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>', pretty_json)
        return "Aucune règle"
    pretty_rules.short_description = 'Aperçu des règles (lecture seule)'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'products_count', 'image_preview']
    list_filter = ['is_active', 'shop']
    search_fields = ['name']
    list_editable = ['order', 'is_active']
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = '📦 Produits'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 4px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'Image'


class ProductCustomizationConfigInline(admin.StackedInline):
    model = ProductCustomizationConfig
    extra = 1
    max_num = 1
    can_delete = False
    filter_horizontal = ['allowed_components', 'allowed_fonts']
    verbose_name = "🛠️ Configuration de l'Atelier Studio"
    verbose_name_plural = "🛠️ Configuration de l'Atelier Studio"
    fieldsets = (
        (None, {
            'fields': (('allowed_components', 'allowed_fonts'), 'studio_config'),
            'description': mark_safe('<div style="color: #666; margin-bottom: 10px;">Sélectionnez les formes et polices autorisées pour cet atelier spécifique.</div>')
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin produit avec gestion complète de la personnalisation
    """
    inlines = [ProductCustomizationConfigInline]
    list_display = [
        'name',
        'category',
        'selling_price',
        'stock_badge',
        'customization_badge',
        'image_preview'
    ]
    list_filter = [
        'is_customizable',
        'is_refundable',
        'category',
        'is_active'
    ]
    search_fields = ['name', 'barcode']
    readonly_fields = ['barcode', 'created_at', 'updated_at', 'profit_margin', 'effective_rules_preview']
    
    fieldsets = (
        ('✨ PERSONNALISATION', {
            'fields': (
                'is_customizable',
                'customization_template',
                'customization_rules_override',
                'effective_rules_preview'
            ),
            'description': mark_safe('''
            <div style="background: #fff3cd; padding: 15px; border-left: 5px solid #ffc107; margin: 10px 0; border-radius: 4px; font-family: sans-serif;">
                <h3 style="margin-top:0; color: #856404; font-size: 16px;">🛠️ Comment activer le Studio Dynamic ?</h3>
                <p style="margin-bottom: 10px; font-size: 13px;">1. Cochez <strong>"Produit personnalisable"</strong><br>
                2. Choisissez un modèle (ex: <strong>Atelier Médaille</strong>)<br>
                3. Configurez les <strong>Composants</strong> et <strong>Polices</strong> tout en bas de cette page.</p>
                <p style="margin-bottom:0; font-size: 11px; opacity: 0.8;">💡 <em>Les composants choisis ici apparaîtront comme des choix d'étapes pour le client.</em></p>
            </div>
            ''')
        }),
        ('📋 Informations de base', {
            'fields': ('name', 'category', 'color_choice', 'custom_color', 'barcode', 'description', 'is_active')
        }),
        ('💰 Prix & Stock', {
            'fields': (
                ('purchase_price', 'selling_price', 'engraving_price', 'profit_margin'),
                ('current_stock', 'minimum_stock')
            )
        }),
        ('🖼️ Images', {
            'fields': ('image', 'secondary_image', 'extra_image_1', 'extra_image_2', 'mockup_image'),
            'description': '<strong>Image mockup</strong> = l\'image servant de base pour le dessin de la gravure en temps réel.'
        }),
        ('⚙️ Règles Spéciales', {
            'fields': ('production_delay_days', 'is_refundable'),
            'classes': ('collapse',)
        }),
        ('📅 Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_badge(self, obj):
        status = obj.stock_status
        colors = {
            'OK': '#4caf50',
            'Faible': '#ff9800',
            'Rupture': '#f44336'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(status, '#999'),
            status
        )
    stock_badge.short_description = 'Stock'
    
    def customization_badge(self, obj):
        if obj.is_customizable:
            if obj.customization_rules_override:
                return format_html('<span style="color: #9c27b0;">⚙️ Règles spécifiques</span>')
            elif obj.customization_template:
                return format_html('<span style="color: #2196f3;">📋 {}</span>', obj.customization_template.name)
            else:
                return format_html('<span style="color: #f44336;">⚠️ Pas de règles</span>')
        return '—'
    customization_badge.short_description = '✨ Personnalisation'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 4px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'Image'
    
    def effective_rules_preview(self, obj):
        """Affiche les règles actives (override > template)"""
        rules = obj.effective_customization_rules
        if rules:
            pretty_json = json.dumps(rules, indent=2, ensure_ascii=False)
            return format_html(
                '<div style="background: #e8f5e9; padding: 15px; border-radius: 4px;"><strong>✅ Règles actives :</strong><pre>{}</pre></div>',
                pretty_json
            )
        return format_html('<div style="background: #ffebee; padding: 15px; border-radius: 4px;">❌ Aucune règle active</div>')
    effective_rules_preview.short_description = 'Aperçu des règles actives'

    class Media:
        js = ('js/admin/admin_customization.js',)


@admin.register(CustomizationPreview)
class CustomizationPreviewAdmin(admin.ModelAdmin):
    """Admin pour voir les previews générées"""
    list_display = ['id', 'product', 'preview_thumbnail', 'created_at']
    list_filter = ['created_at', 'product']
    readonly_fields = ['product', 'customization_data', 'preview_image', 'created_at', 'pretty_data']
    
    def preview_thumbnail(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.preview_image.url)
        return '—'
    preview_thumbnail.short_description = 'Aperçu'
    
    def pretty_data(self, obj):
        if obj.customization_data:
            pretty_json = json.dumps(obj.customization_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px;">{}</pre>', pretty_json)
        return '—'
    pretty_data.short_description = 'Données (formaté)'


@admin.register(CustomizationFont)
class CustomizationFontAdmin(admin.ModelAdmin):
    list_display = ['name', 'font_family', 'is_active', 'preview_sample']
    list_editable = ['is_active']
    
    def preview_sample(self, obj):
        return format_html(
            '<span style="font-family: {}; font-size: 16px;">Exemple de texte : ABC abc 123</span>',
            obj.font_family
        )
    preview_sample.short_description = 'Aperçu'


@admin.register(CustomizableComponent)
class CustomizableComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'component_type', 'base_price_modifier', 'is_active', 'image_preview']
    list_filter = ['component_type', 'is_active']
    list_editable = ['is_active', 'base_price_modifier']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 4px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'Image'

@admin.register(ProductCustomizationConfig)
class ProductCustomizationConfigAdmin(admin.ModelAdmin):
    list_display = ['product', 'get_fonts_count', 'get_components_count']
    filter_horizontal = ['allowed_components', 'allowed_fonts']
    
    def get_fonts_count(self, obj):
        return obj.allowed_fonts.count()
    get_fonts_count.short_description = 'Polices'
    
    def get_components_count(self, obj):
        return obj.allowed_components.count()
    get_components_count.short_description = 'Composants'
