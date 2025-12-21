from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from accounts.models import Shop


class Category(models.Model):
    """Catégorie de produits (ex: Boissons, Alimentaire, Hygiène)"""
    
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(
        max_length=100,
        verbose_name="Nom de la catégorie"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name="Image de la catégorie",
        help_text="Image affichée sur la page d'accueil"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Afficher sur la page d'accueil",
        help_text="Cochez pour afficher cette catégorie dans la section showcase"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Les catégories sont triées par ordre croissant"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['order', 'name']
        unique_together = ['shop', 'name']  # Unique par boutique
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Produit en vente dans le magasin"""
    
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(
        max_length=200,
        verbose_name="Nom du produit"
    )
    barcode = models.CharField(
        max_length=13,
        verbose_name="Code-barres",
        help_text="Code-barres unique du produit (EAN-13)",
        blank=True  # Allow empty in forms, auto-generated in save()
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Catégorie",
        default=6
    )
    
    # Prix
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Prix d'achat",
        help_text="Prix d'achat unitaire HT"
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Prix de vente",
        help_text="Prix de vente TTC"
    )
    
    # Stock
    current_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock actuel"
    )
    minimum_stock = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name="Stock minimum",
        help_text="Seuil d'alerte pour réapprovisionnement"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Produit disponible à la vente"
    )
    
    # Métadonnées
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name="Image du produit"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['name']
        unique_together = ['shop', 'barcode']  # Unique par boutique
    
    def __str__(self):
        return f"{self.name} ({self.barcode})"
    
    @property
    def profit_margin(self):
        """Calcule la marge bénéficiaire en pourcentage"""
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        """Vérifie si le stock est en dessous du seuil minimum"""
        return self.current_stock <= self.minimum_stock
    
    @property
    def stock_status(self):
        """Retourne le statut du stock (OK, Faible, Rupture)"""
        if self.current_stock == 0:
            return "Rupture"
        elif self.is_low_stock:
            return "Faible"
        return "OK"
    
    def generate_barcode(self):
        """Génère un code-barres EAN-13 unique"""
        import random
        while True:
            # Générer 12 chiffres aléatoires (le 13ème est le checksum)
            code = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            # Calculer le checksum EAN-13
            checksum = self._calculate_ean13_checksum(code)
            barcode = code + str(checksum)
            # Vérifier l'unicité
            if not Product.objects.filter(barcode=barcode).exists():
                return barcode
    
    def _calculate_ean13_checksum(self, code):
        """Calcule le checksum pour un code EAN-13"""
        odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
        even_sum = sum(int(code[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        checksum = (10 - (total % 10)) % 10
        return checksum
    
    def save(self, *args, **kwargs):
        """Override save to generate barcode if not provided"""
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)
