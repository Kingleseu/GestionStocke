from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from accounts.models import Shop
import random


class CustomizationTemplate(models.Model):
    """
    Template réutilisable de règles de personnalisation.
    Ex: "Gravure Simple", "Gravure + Forme", "Upload Image"
    """
    name = models.CharField(max_length=100, verbose_name="Nom du modèle")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Règles JSON complètes
    rules = models.JSONField(
        default=dict,
        verbose_name="Règles JSON",
        help_text="""
        Structure:
        {
          "version": "2.0",
          "zones": [
            {
              "id": "text_zone",
              "type": "text|selection|image|shape",
              "label": "Gravure",
              "required": true,
              "conditions": {"autre_zone": "valeur"},
              "constraints": {
                "max_length": 20,
                "allowed_chars": "regex",
                "allowed_fonts": ["Arial", "Cursive"]
              },
              "price_formula": {
                "base": 5.00,
                "per_char": 0.50
              },
              "preview_config": {
                "position": {"x": 50, "y": 50},
                "size": 20,
                "color": "#000000"
              }
            }
          ],
          "special_rules": {
            "non_refundable": true,
            "production_delay_days": 3,
            "legal_notice": "Produit personnalisé non repris"
          }
        }
        """
    )
    
    # Métadonnées
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modèle de Personnalisation"
        verbose_name_plural = "Modèles de Personnalisation"
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Catégorie de produits"""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Nom")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Image")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['order', 'name']
        unique_together = ['shop', 'name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Produit (standard ou personnalisable)"""
    COLOR_CHOICES = [
        ('argent', 'Argent'),
        ('or', 'Or'),
        ('autre', 'Autre'),
    ]
    ENGRAVING_MODE_CHOICES = [
        ('text', 'Texte uniquement'),
        ('image', 'Image / Photo uniquement'),
        ('both', 'Texte + Image'),
    ]
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="Nom")
    barcode = models.CharField(max_length=13, verbose_name="Code-barres", blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Catégorie", default=6)
    color_choice = models.CharField(max_length=20, choices=COLOR_CHOICES, default='argent', verbose_name="Couleur")
    custom_color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Couleur personnalis??e")
    
    # Prix
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Prix d'achat")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Prix de vente")
    engraving_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Prix de gravure")
    
    # Stock
    current_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Stock actuel")
    minimum_stock = models.IntegerField(default=5, validators=[MinValueValidator(0)], verbose_name="Stock minimum")
    
    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Images
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image principale")
    secondary_image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image au survol")
    extra_image_1 = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image supplémentaire 1")
    extra_image_2 = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image supplémentaire 2")
    mockup_image = models.ImageField(
        upload_to='products/mockups/', 
        blank=True, 
        null=True,
        verbose_name="Image Mockup (pour preview)",
        help_text="Image de base pour la prévisualisation de personnalisation"
    )
    
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # === PERSONNALISATION ===
    is_customizable = models.BooleanField(
        default=False,
        verbose_name="Produit personnalisable",
        help_text="Active la personnalisation sur la boutique"
    )
    engraving_mode = models.CharField(
        max_length=10,
        choices=ENGRAVING_MODE_CHOICES,
        default='text',
        verbose_name="Type de gravure"
    )
    
    customization_template = models.ForeignKey(
        CustomizationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name="Modèle de personnalisation"
    )
    
    # Surcharge des règles (optionnel, prioritaire sur le template)
    customization_rules_override = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Règles spécifiques (Surcharge)",
        help_text="Si rempli, ignore le template et utilise ces règles"
    )
    
    # Règles spéciales
    production_delay_days = models.PositiveIntegerField(
        default=0,
        verbose_name="Délai de production (jours)",
        help_text="Jours additionnels pour fabriquer ce produit personnalisé"
    )
    
    is_refundable = models.BooleanField(
        default=True,
        verbose_name="Produit remboursable",
        help_text="Décocher pour les produits personnalisés non repris"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['name']
        unique_together = ['shop', 'barcode']
    
    def __str__(self):
        return f"{self.name} ({self.barcode})"
    
    @property
    def effective_customization_rules(self):
        """Retourne les règles actives (Atelier > override > template)"""
        from .services import CustomizationService
        return CustomizationService.get_product_rules(self)
    
    @property
    def profit_margin(self):
        """Marge bénéficiaire en %"""
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock
    
    @property
    def stock_status(self):
        if self.current_stock == 0:
            return "Rupture"
        elif self.is_low_stock:
            return "Faible"
        return "OK"
    
    def generate_barcode(self):
        """Génère un code-barres EAN-13 unique"""
        while True:
            code = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            checksum = self._calculate_ean13_checksum(code)
            barcode = code + str(checksum)
            if not Product.objects.filter(barcode=barcode).exists():
                return barcode
    
    def _calculate_ean13_checksum(self, code):
        odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
        even_sum = sum(int(code[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        checksum = (10 - (total % 10)) % 10
        return checksum
    
    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)


class CustomizationPreview(models.Model):
    """
    Preview générée d'une personnalisation.
    Stockée pour éviter de recalculer et pour traçabilité.
    """
    # Lien optionnel vers un CartItem ou OrderItem
    # (on peut aussi créer des previews à la volée sans les sauvegarder)
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produit")
    customization_data = models.JSONField(verbose_name="Données de personnalisation")
    
    # Image générée
    preview_image = models.ImageField(
        upload_to='previews/',
        verbose_name="Image de prévisualisation"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Prévisualisation"
        verbose_name_plural = "Prévisualisations"
    
    def __str__(self):
        return f"Preview {self.id} - {self.product.name}"


class CustomizationFont(models.Model):
    """
    Polices de caractères disponibles pour la gravure.
    """
    name = models.CharField(max_length=50, verbose_name="Nom de la police")
    font_family = models.CharField(max_length=100, verbose_name="Famille CSS (ex: 'Dancing Script', cursive)")
    font_url = models.URLField(blank=True, verbose_name="URL Google Fonts (optionnel)")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Police de Gravure"
        verbose_name_plural = "Polices de Gravure"


class CustomizableComponent(models.Model):
    """
    Composants individuels (Médaillons, Breloques) utilisables pour la personnalisation.
    """
    TYPE_CHOICES = [
        ('medallion', 'Médaillon'),
        ('charm', 'Breloque'),
        ('bead', 'Perle'),
    ]
    name = models.CharField(max_length=100, verbose_name="Nom du composant")
    component_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='medallion')
    
    # Image du composant seul (utilisée pour le choix et la preview)
    image = models.ImageField(upload_to='customization/components/', verbose_name="Image du composant")
    
    # Forme (utilisée pour les calculs géométriques ou icônes)
    shape_identifier = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Identifiant pour le JS (ex: 'heart', 'star', 'round', 'dogtag', 'africa', 'cross', 'bar_active')"
    )
    
    base_price_modifier = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Surcoût de base"
    )
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Composant de Personnalisation"
        verbose_name_plural = "Composants de Personnalisation"


class ProductCustomizationConfig(models.Model):
    """
    Configuration spécifique d'Atelier pour un Produit.
    Lien entre le produit et ses composants/polices autorisés.
    """
    product = models.OneToOneField(
        Product, 
        on_delete=models.CASCADE, 
        related_name='customization_config',
        verbose_name="Produit"
    )
    
    allowed_components = models.ManyToManyField(
        CustomizableComponent, 
        blank=True, 
        verbose_name="Composants autorisés"
    )
    
    allowed_fonts = models.ManyToManyField(
        CustomizationFont, 
        blank=True, 
        verbose_name="Polices autorisées"
    )
    
    # Configuration visuelle pour le studio (JSON pour flexibilité)
    # Ex: {"max_components": 3, "zones": [{"id": "main", "pos": {"x": 50, "y": 50}}]}
    studio_config = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name="Configuration Atelier (JSON)"
    )

    def __str__(self):
        return f"Config Atelier: {self.product.name}"

    class Meta:
        verbose_name = "Configuration Atelier"
        verbose_name_plural = "Configurations Atelier"
