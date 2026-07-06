from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import Shop


class SupplyCategory(models.Model):
    """
    Catégorie de produits pour l'approvisionnement PEMBENY.
    Création séparée comme dans le système e-commerce.
    """
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(upload_to='supply/categories/', blank=True, null=True, verbose_name="Image")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Catégorie fournisseur"
        verbose_name_plural = "Catégories fournisseurs"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Fournisseur PEMBENY avec logo et catégorie"""
    CATEGORY_CHOICES = [
        ('beverages', 'Boissons'),
        ('food', 'Alimentaire'),
        ('hygiene', 'Hygiene'),
        ('flour', 'Farine et cereales'),
        ('snacks', 'Snacks'),
        ('other', 'Autre'),
    ]

    name = models.CharField(max_length=160, verbose_name='Nom du fournisseur')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other', verbose_name='Catégorie')
    supply_category = models.ForeignKey(
        SupplyCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suppliers',
        verbose_name="Catégorie PEMBENY"
    )
    contact_name = models.CharField(max_length=120, blank=True, verbose_name='Nom du contact')
    phone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Adresse')
    logo = models.ImageField(upload_to='supply/suppliers/', blank=True, null=True, verbose_name='Logo du fournisseur')
    description = models.TextField(blank=True, verbose_name='Description')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Fournisseur PEMBENY'
        verbose_name_plural = 'Fournisseurs PEMBENY'

    def __str__(self):
        return self.name

    @property
    def active_products_count(self):
        return self.products.filter(is_active=True).count()


class SupplySiteSettings(models.Model):
    brand_name = models.CharField(max_length=80, default='PEMBENY')
    brand_signature = models.CharField(max_length=120, default='By Dellions Group')
    hero_badge = models.CharField(max_length=160, default='Reseau B2B Kinshasa')
    hero_title = models.CharField(max_length=220, default='Approvisionnez votre boutique depuis les fournisseurs partenaires.')
    hero_subtitle = models.TextField(
        default='Catalogue centralise, stock par hub, panier rapide, paiement flexible et suivi de livraison vers votre point de vente.'
    )
    primary_cta_text = models.CharField(max_length=80, default='Creer ma boutique')
    primary_cta_url = models.CharField(max_length=200, default='/supply/register/')
    secondary_cta_text = models.CharField(max_length=80, default='Voir le catalogue')
    secondary_cta_url = models.CharField(max_length=200, default='#catalogue')
    network_title = models.CharField(max_length=160, default='Comment PEMBENY organise votre approvisionnement')
    network_subtitle = models.TextField(
        default='PEMBENY connecte les fournisseurs, les hubs de distribution et les boutiques dans une seule experience.'
    )
    contact_phone = models.CharField(max_length=50, default='(+243) 0829959698')
    footer_text = models.CharField(max_length=180, default='PEMBENY / Dellions Group SARL - Kinshasa')
    logo = models.ImageField(upload_to='supply/site/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuration site PEMBENY'
        verbose_name_plural = 'Configuration site PEMBENY'

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return 'Configuration publique PEMBENY'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SupplyHomepageStat(models.Model):
    value = models.CharField(max_length=40)
    label = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Statistique accueil PEMBENY'
        verbose_name_plural = 'Statistiques accueil PEMBENY'

    def __str__(self):
        return f'{self.value} - {self.label}'


class SupplyHomeFeature(models.Model):
    icon_class = models.CharField(max_length=60, default='bi-box-seam')
    title = models.CharField(max_length=120)
    body = models.TextField()
    badge = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Carte avantage PEMBENY'
        verbose_name_plural = 'Cartes avantages PEMBENY'

    def __str__(self):
        return self.title


class SupplyProcessStep(models.Model):
    number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=120)
    body = models.TextField()
    icon_class = models.CharField(max_length=60, default='bi-check-circle')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'number', 'id']
        verbose_name = 'Etape processus PEMBENY'
        verbose_name_plural = 'Etapes processus PEMBENY'

    def __str__(self):
        return f'{self.number}. {self.title}'


class Hub(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    commune = models.CharField(max_length=80)
    address = models.TextField(blank=True)
    coverage_communes = models.JSONField(default=list, blank=True)
    manager_phone = models.CharField(max_length=50, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Hub PEMBENY'
        verbose_name_plural = 'Hubs PEMBENY'

    def __str__(self):
        return f'{self.name} ({self.commune})'

    def handles_commune(self, commune):
        target = (commune or '').strip().lower()
        return any(str(item).strip().lower() == target for item in self.coverage_communes)


class SupplyProduct(models.Model):
    """Produit d'approvisionnement avec image et catégorie PEMBENY"""
    CATEGORY_CHOICES = Supplier.CATEGORY_CHOICES
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('CDF', 'CDF'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='products', verbose_name='Fournisseur')
    name = models.CharField(max_length=180, verbose_name='Nom du produit')
    brand = models.CharField(max_length=120, blank=True, verbose_name='Marque')
    sku = models.CharField(max_length=80, blank=True, verbose_name='SKU / Référence')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other', verbose_name='Catégorie')
    supply_category = models.ForeignKey(
        SupplyCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Catégorie PEMBENY'
    )
    unit_label = models.CharField(max_length=120, verbose_name='Unité de vente', help_text='Ex: caisse 24 bouteilles, carton 40 paquets')
    package_size = models.PositiveIntegerField(default=1, verbose_name='Taille du package')
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Prix de gros')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD', verbose_name='Devise')
    minimum_order_quantity = models.PositiveIntegerField(default=1, verbose_name='Quantité minimum de commande')
    image = models.ImageField(upload_to='supply/products/', blank=True, null=True, verbose_name='Image du produit')
    description = models.TextField(blank=True, verbose_name='Description du produit')
    icon_class = models.CharField(max_length=60, default='bi-box-seam', verbose_name='Icône')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    is_featured = models.BooleanField(default=False, verbose_name='Mis en avant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['supplier__name', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['supplier', 'is_active']),
        ]
        verbose_name = 'Produit approvisionnement'
        verbose_name_plural = 'Produits approvisionnement'

    def __str__(self):
        return f'{self.name} - {self.supplier.name}'

    @property
    def price_label(self):
        suffix = '$' if self.currency == 'USD' else 'FC'
        value = int(self.wholesale_price) if self.wholesale_price == self.wholesale_price.to_integral() else self.wholesale_price
        return f'{value} {suffix}'


class HubInventory(models.Model):
    hub = models.ForeignKey(Hub, on_delete=models.CASCADE, related_name='inventories')
    product = models.ForeignKey(SupplyProduct, on_delete=models.CASCADE, related_name='hub_inventories')
    available_quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['hub', 'product']
        ordering = ['hub__name', 'product__name']
        indexes = [
            models.Index(fields=['hub', 'product']),
            models.Index(fields=['available_quantity', 'reserved_quantity']),
        ]
        verbose_name = 'Stock hub'
        verbose_name_plural = 'Stocks hubs'

    def __str__(self):
        return f'{self.product.name} @ {self.hub.code}'

    @property
    def sellable_quantity(self):
        return max(self.available_quantity - self.reserved_quantity, 0)

    @property
    def stock_status(self):
        if self.sellable_quantity == 0:
            return 'out'
        if self.sellable_quantity <= self.reorder_threshold:
            return 'low'
        return 'ok'

    def reserve(self, quantity, commit=True):
        quantity = int(quantity)
        if quantity > self.sellable_quantity:
            raise ValueError('Stock hub insuffisant')
        self.reserved_quantity += quantity
        if commit:
            self.save(update_fields=['reserved_quantity', 'updated_at'])


class MerchantAccount(models.Model):
    SHOP_TYPE_DEPOT = 'depot_wholesaler'
    SHOP_TYPE_NEIGHBORHOOD = 'neighborhood_shop'
    SHOP_TYPE_BREWERY = 'brewery_shop'
    SHOP_TYPE_PHARMACY = 'pharmacy_drugstore'
    SHOP_TYPE_HARDWARE = 'hardware_store'
    SHOP_TYPE_OTHER = 'other'
    SHOP_TYPE_CHOICES = [
        (SHOP_TYPE_DEPOT, 'Depot / Grossiste'),
        (SHOP_TYPE_NEIGHBORHOOD, 'Boutique de quartier'),
        (SHOP_TYPE_BREWERY, 'Boutique brassicole'),
        (SHOP_TYPE_PHARMACY, 'Pharmacie / Drugstore'),
        (SHOP_TYPE_HARDWARE, 'Quincaillerie'),
        (SHOP_TYPE_OTHER, 'Autre'),
    ]

    AGE_UNDER_3_MONTHS = 'under_3_months'
    AGE_3_TO_6_MONTHS = '3_to_6_months'
    AGE_6_TO_12_MONTHS = '6_to_12_months'
    AGE_OVER_12_MONTHS = 'over_12_months'
    BUSINESS_AGE_CHOICES = [
        (AGE_UNDER_3_MONTHS, 'Moins de 3 mois'),
        (AGE_3_TO_6_MONTHS, '3 a 6 mois'),
        (AGE_6_TO_12_MONTHS, '6 a 12 mois'),
        (AGE_OVER_12_MONTHS, 'Plus de 12 mois'),
    ]
    PREQUALIFIED_AGES = {AGE_6_TO_12_MONTHS, AGE_OVER_12_MONTHS}

    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='merchant_account')
    owner_full_name = models.CharField(max_length=180, blank=True)
    commune = models.CharField(max_length=80, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    secondary_phone = models.CharField(max_length=50, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    whatsapp_active = models.BooleanField(default=True)
    shop_type = models.CharField(max_length=40, choices=SHOP_TYPE_CHOICES, default=SHOP_TYPE_NEIGHBORHOOD)
    business_age = models.CharField(max_length=40, choices=BUSINESS_AGE_CHOICES, default=AGE_6_TO_12_MONTHS)
    storefront_photo = models.ImageField(upload_to='supply/storefronts/', blank=True, null=True)
    preferred_hub = models.ForeignKey(Hub, on_delete=models.SET_NULL, null=True, blank=True, related_name='merchant_accounts')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credit_used = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_credit_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Compte boutique PEMBENY'
        verbose_name_plural = 'Comptes boutiques PEMBENY'

    def __str__(self):
        return f'Compte PEMBENY - {self.shop.name}'

    @property
    def credit_available(self):
        return max(self.credit_limit - self.credit_used, Decimal('0.00'))

    @property
    def is_prequalified(self):
        return self.business_age in self.PREQUALIFIED_AGES

    @property
    def prequalification_label(self):
        return 'Prequalifie' if self.is_prequalified else 'A verifier'


class ProcurementOrder(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Paiement en attente'),
        ('awaiting_preparation', 'En attente de preparation'),
        ('preparing', 'Preparation au hub'),
        ('ready_for_dispatch', 'Prete pour expedition'),
        ('out_for_delivery', 'En livraison'),
        ('delivered', 'Livree'),
        ('cancelled', 'Annulee'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('m-pesa', 'M-Pesa'),
        ('airtel', 'Airtel Money'),
        ('orange', 'Orange Money'),
        ('bank', 'Virement bancaire'),
        ('credit', 'Credit marchandises'),
        ('delivery-cash', 'Paiement a la livraison'),
    ]

    order_number = models.CharField(max_length=30, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='procurement_orders')
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True, related_name='procurement_orders')
    hub = models.ForeignKey(Hub, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    merchant_name = models.CharField(max_length=180)
    commune = models.CharField(max_length=80)
    delivery_address = models.TextField()
    contact_phone = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='m-pesa')
    payment_reference = models.CharField(max_length=100, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_payment')
    delivery_eta = models.DateTimeField(null=True, blank=True)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    escrow_released = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['shop', 'created_at']),
            models.Index(fields=['hub', 'status']),
        ]
        verbose_name = 'Commande approvisionnement'
        verbose_name_plural = 'Commandes approvisionnement'

    def __str__(self):
        return f'{self.tracking_reference} - {self.merchant_name}'

    @property
    def tracking_reference(self):
        return self.order_number or f'PB-{self.pk or "NEW"}'

    def _build_order_number(self):
        created_at = timezone.localtime(self.created_at or timezone.now())
        return f'PB-{created_at.strftime("%Y%m%d")}-{self.pk:06d}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pk and not self.order_number:
            self.order_number = self._build_order_number()
            type(self).objects.filter(pk=self.pk).update(order_number=self.order_number)

    def get_absolute_url(self):
        return reverse('supply:order_detail', args=[self.tracking_reference])

    def recalculate_totals(self, commit=True):
        subtotal = sum((item.line_total for item in self.items.all()), Decimal('0.00'))
        self.subtotal = subtotal
        self.total_amount = subtotal + self.delivery_fee
        if commit:
            self.save(update_fields=['subtotal', 'total_amount', 'updated_at'])
        return self.total_amount


class ProcurementOrderItem(models.Model):
    order = models.ForeignKey(ProcurementOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(SupplyProduct, on_delete=models.SET_NULL, null=True, related_name='order_items')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=180)
    supplier_name = models.CharField(max_length=160, blank=True)
    unit_label = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Ligne approvisionnement'
        verbose_name_plural = 'Lignes approvisionnement'

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

    def save(self, *args, **kwargs):
        if self.product:
            self.product_name = self.product_name or self.product.name
            self.unit_label = self.unit_label or self.product.unit_label
            if not self.supplier:
                self.supplier = self.product.supplier
            if not self.supplier_name:
                self.supplier_name = self.product.supplier.name
        self.line_total = Decimal(str(self.quantity)) * self.unit_price
        super().save(*args, **kwargs)


class OrderTrackingEvent(models.Model):
    order = models.ForeignKey(ProcurementOrder, on_delete=models.CASCADE, related_name='tracking_events')
    status = models.CharField(max_length=30, choices=ProcurementOrder.STATUS_CHOICES)
    label = models.CharField(max_length=160)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Evenement de suivi'
        verbose_name_plural = 'Evenements de suivi'

    def __str__(self):
        return f'{self.order.tracking_reference} - {self.label}'