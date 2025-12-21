from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from products.models import Product
from accounts.models import Shop


class Purchase(models.Model):
    """Achat de marchandises auprès d'un fournisseur"""
    
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name="Boutique",
        null=True,
        blank=True
    )
    
    # Informations de base
    purchase_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'achat"
    )
    supplier = models.CharField(
        max_length=200,
        verbose_name="Fournisseur",
        help_text="Nom du fournisseur"
    )
    
    # Montant
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total"
    )
    
    # Métadonnées
    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Numéro de facture"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchases',
        verbose_name="Créé par"
    )
    is_received = models.BooleanField(
        default=False,
        verbose_name="Marchandise reçue",
        help_text="Cocher quand la marchandise est réceptionnée"
    )
    
    class Meta:
        verbose_name = "Achat"
        verbose_name_plural = "Achats"
        ordering = ['-purchase_date']
    
    def __str__(self):
        return f"Achat #{self.id} - {self.supplier} - {self.purchase_date.strftime('%d/%m/%Y')} - {self.total}$"
    
    def calculate_total(self):
        """Calcule le total de l'achat à partir des items"""
        total = sum(item.subtotal for item in self.items.all())
        self.total = total
        return total
    
    def save(self, *args, **kwargs):
        """Override save pour recalculer le total automatiquement"""
        if self.pk:  # Si l'achat existe déjà
            self.calculate_total()
        super().save(*args, **kwargs)
    
    @property
    def item_count(self):
        """Retourne le nombre total d'articles achetés"""
        return sum(item.quantity for item in self.items.all())


class PurchaseItem(models.Model):
    """Ligne d'achat (article acheté dans un achat)"""
    
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Achat"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_items',
        verbose_name="Produit"
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantité"
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Prix d'achat unitaire",
        help_text="Prix d'achat au moment de la commande"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Sous-total"
    )
    
    class Meta:
        verbose_name = "Ligne d'achat"
        verbose_name_plural = "Lignes d'achat"
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity} - {self.subtotal}$"
    
    def save(self, *args, **kwargs):
        """Calcule automatiquement le sous-total et met à jour le stock"""
        # Calculer le sous-total
        self.subtotal = self.quantity * self.purchase_price
        
        # Sauvegarder l'item
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Ajouter au stock si l'achat est marqué comme reçu
        if is_new and self.purchase.is_received:
            self.product.current_stock += self.quantity
            self.product.save()
        
        # Recalculer le total de l'achat
        self.purchase.calculate_total()
        self.purchase.save()
