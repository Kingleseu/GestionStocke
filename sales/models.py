from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from products.models import Product
from accounts.models import Shop


class Sale(models.Model):
    """Vente effectuée à la caisse"""
    
    PAYMENT_METHODS = [
        ('CASH', 'Espèces'),
        ('CARD', 'Carte bancaire'),
        ('CHECK', 'Chèque'),
        ('MOBILE', 'Paiement mobile'),
        ('OTHER', 'Autre'),
    ]
    
    # Informations de base
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='sales',
        verbose_name="Boutique",
        null=True,  # For migration compatibility
        blank=True
    )
    sale_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de vente"
    )
    cashier = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name="Caissier"
    )
    
    # Paiement
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        default='CASH',
        verbose_name="Mode de paiement"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total"
    )
    
    # Métadonnées
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name="Vente annulée"
    )
    
    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-sale_date']
    
    def __str__(self):
        return f"Vente #{self.id} - {self.sale_date.strftime('%d/%m/%Y %H:%M')} - {self.total} FC"
    
    def calculate_total(self):
        """Calcule le total de la vente à partir des items"""
        total = sum(item.subtotal for item in self.items.all())
        self.total = total
        return total
    
    def save(self, *args, **kwargs):
        """Override save pour recalculer le total automatiquement"""
        if self.pk:  # Si la vente existe déjà
            self.calculate_total()
        super().save(*args, **kwargs)
    
    @property
    def item_count(self):
        """Retourne le nombre total d'articles vendus"""
        return sum(item.quantity for item in self.items.all())


class SaleItem(models.Model):
    """Ligne de vente (article vendu dans une vente)"""
    
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Vente"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='sale_items',
        verbose_name="Produit"
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantité"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Prix unitaire",
        help_text="Prix au moment de la vente"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Sous-total"
    )
    
    class Meta:
        verbose_name = "Ligne de vente"
        verbose_name_plural = "Lignes de vente"
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity} - {self.subtotal} FC"
    
    def save(self, *args, **kwargs):
        """Calcule automatiquement le sous-total et met à jour le stock"""
        # Calculer le sous-total
        self.subtotal = self.quantity * self.unit_price
        
        # Sauvegarder l'item
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Déduire du stock si c'est une nouvelle vente
        if is_new and not self.sale.is_cancelled:
            self.product.current_stock -= self.quantity
            self.product.save()
        
        # Recalculer le total de la vente
        self.sale.calculate_total()
        self.sale.save()
