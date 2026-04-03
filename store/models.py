from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from products.models import Product

class StoreSettings(models.Model):
    """
    Singleton model for store configuration.
    """
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Frais de livraison")

    def save(self, *args, **kwargs):
        if not self.pk and StoreSettings.objects.exists():
            self.pk = StoreSettings.objects.first().pk
        return super(StoreSettings, self).save(*args, **kwargs)

    def __str__(self):
        return "Configuration du Site"

    class Meta:
        verbose_name = "Configuration Site"
        verbose_name_plural = "Configuration Site"


class CustomerProfile(models.Model):
    """
    Extended profile for store customers (separate from internal staff profile).
    Stores shipping defaults.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"Customer: {self.user.username}"

class Cart(models.Model):
    """
    Represents a shopping cart. 
    Can be linked to a user or just a session_id for guests.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Cart ({self.id})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    # === PERSONNALISATION ===
    customization_data = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Données de personnalisation",
        help_text="Structure: {'choices': {'zone_id': value}}"
    )
    
    # Prix figé (sécurité)
    price_at_addition = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prix unitaire figé",
        help_text="Prix Base + Options au moment de l'ajout"
    )
    
    # Preview générée (optionnelle)
    preview_image = models.ImageField(
        upload_to='cart_previews/',
        blank=True,
        null=True,
        verbose_name="Aperçu personnalisation"
    )
    
    # Données de production (générées à la commande)
    production_data = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Instructions de production"
    )

    def save(self, *args, **kwargs):
        # Si c'est un nouvel item et qu'on n'a pas encore fixé le prix
        if not self.pk and self.price_at_addition is None and self.product:
             # Fallback simple (le vrai calcul doit se faire via le Service avant le save)
             self.price_at_addition = self.product.selling_price
        super().save(*args, **kwargs)

    def total_price(self):
        # On utilise le prix figé s'il existe, sinon le calcul dynamique (old way)
        unit_price = self.price_at_addition
        if unit_price is None:
             unit_price = self.product.selling_price
        
        return unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class DeliveryZone(models.Model):
    """
    Zones de livraison configurables par l'administration.
    """
    name = models.CharField(max_length=100, verbose_name="Nom de la zone")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Tarif de livraison")
    is_active = models.BooleanField(default=True, verbose_name="Zone active ?")

    class Meta:
        verbose_name = "Zone de Livraison"
        verbose_name_plural = "Zones de Livraison"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.price} FC"


ORDER_PAYMENT_METHOD_CHOICES = [
    ('m-pesa', 'M-Pesa'),
    ('airtel', 'Airtel Money'),
    ('orange', 'Orange Money'),
    ('virement', 'Virement Bancaire'),
    ('cash', 'Paiement en Boutique'),
    ('delivery-cash', 'Paiement a la Livraison'),
]

class WebOrder(models.Model):
    """
    A completed order placed via the website.
    """
    STATUS_CHOICES = [
        ('pending_payment', 'En attente de paiement'),
        ('awaiting_verification', 'En attente de vérification'),
        ('paid', 'Payé'),
        ('cancelled', 'Annulé'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=20, choices=ORDER_PAYMENT_METHOD_CHOICES, default='m-pesa')
    order_number = models.CharField(max_length=30, unique=True, blank=True, verbose_name="Reference commande")
    delivery_confirmation_code = models.CharField(max_length=12, blank=True, verbose_name="Code de remise")
    
    delivery_type = models.CharField(max_length=20, choices=[('pickup', 'Retrait en boutique'), ('delivery', 'Livraison à domicile')], default='delivery', verbose_name="Type de livraison")
    delivery_zone = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zone de livraison sélectionnée")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Frais de livraison appliqués")
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_payment')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        reference = self.order_number or f"#{self.id}"
        return f"Order {reference} - {self.full_name} ({self.get_status_display()})"

    @property
    def requires_manual_payment_proof(self):
        return self.payment_method not in {'cash', 'delivery-cash'}

    @property
    def is_cash_on_delivery(self):
        return self.payment_method == 'delivery-cash'

    @property
    def tracking_reference(self):
        return self.order_number or f"CMD-{self.pk or 'NEW'}"

    @property
    def items_subtotal(self):
        return sum((item.line_total for item in self.items.all()), start=0)

    def get_customer_order_url(self):
        return reverse('store:account_order_detail', args=[self.tracking_reference])

    def _build_order_number(self):
        created_at = timezone.localtime(self.created_at or timezone.now())
        return f"CMD-{created_at.strftime('%Y%m%d')}-{self.pk:06d}"

    def _build_delivery_confirmation_code(self):
        return get_random_string(8, allowed_chars='23456789ABCDEFGHJKLMNPQRSTUVWXYZ')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        updates = {}
        if self.pk and not self.order_number:
            updates['order_number'] = self._build_order_number()

        if self.payment_method == 'delivery-cash' and not self.delivery_confirmation_code:
            updates['delivery_confirmation_code'] = self._build_delivery_confirmation_code()
        elif self.payment_method != 'delivery-cash' and self.delivery_confirmation_code:
            updates['delivery_confirmation_code'] = ''

        if updates:
            type(self).objects.filter(pk=self.pk).update(**updates)
            for field, value in updates.items():
                setattr(self, field, value)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

class ManualPayment(models.Model):
    PAYMENT_METHODS = [
        ('m-pesa', 'M-Pesa'),
        ('airtel', 'Airtel Money'),
        ('orange', 'Orange Money'),
        ('virement', 'Virement Bancaire'),
        ('cash', 'Paiement en Boutique'),
        ('delivery-cash', 'Paiement à la Livraison'),
    ]
    
    STATUS_CHOICES = [
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]

    order = models.OneToOneField(WebOrder, on_delete=models.CASCADE, related_name='manual_payment')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_ref = models.CharField(max_length=100, verbose_name="Référence Transaction")
    proof_file = models.FileField(upload_to='payment_proofs/', verbose_name="Preuve de paiement")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Motif de rejet")
    
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Paiement pour Commande {self.order.id} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = "Paiement Manuel"
        verbose_name_plural = "Paiements Manuels"
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

class WebOrderItem(models.Model):
    """Item de commande avec snapshot complet (prix, personnalisation, production)"""
    order = models.ForeignKey(WebOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200, blank=True, default='', verbose_name="Nom produit (snapshot)")  # Au cas où product supprimé
    quantity = models.PositiveIntegerField()
    
    # Prix figé
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix unitaire (snapshot)"
    )
    
    # Personnalisation
    customization_data = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Données personnalisation"
    )
    
    # Preview sauvegardée
    preview_image = models.ImageField(
        upload_to='order_previews/',
        blank=True,
        null=True,
        verbose_name="Aperçu personnalisation"
    )

    # Photo client originale
    client_image = models.ImageField(
        upload_to='order_client_photos/',
        blank=True,
        null=True,
        verbose_name="Photo client originale"
    )
    
    # Données pour l'atelier
    production_data = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Instructions atelier",
        help_text="Instructions de création/gravure/impression"
    )
    
    def __str__(self):
        name = self.product.name if self.product else self.product_name
        return f"{self.quantity} x {name}"

    @property
    def line_total(self):
        return self.price * self.quantity
    
    def save(self, *args, **kwargs):
        # Sauvegarder le nom du produit au moment de la commande
        if self.product and not self.product_name:
            self.product_name = self.product.name
        super().save(*args, **kwargs)


class AdminNotification(models.Model):
    """Notification interne visible dans la cloche d'administration."""

    TYPE_CHOICES = [
        ('new_order', 'Nouvelle commande'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_notifications',
    )
    order = models.ForeignKey(
        WebOrder,
        on_delete=models.CASCADE,
        related_name='admin_notifications',
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='new_order')
    title = models.CharField(max_length=140)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification admin"
        verbose_name_plural = "Notifications admin"
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
        ]


class StorePickupVoucher(models.Model):
    """
    Bon de retrait pour les clients qui paient en boutique.
    Généré automatiquement lors de la création de la commande si payment_method='cash'.
    """
    order = models.OneToOneField(WebOrder, on_delete=models.CASCADE, related_name='pickup_voucher')
    voucher_number = models.CharField(max_length=30, unique=True, blank=True, verbose_name="Numéro du bon")
    pickup_code = models.CharField(max_length=8, blank=True, verbose_name="Code de récupération")
    
    # QR Code (généré automatiquement)
    qr_code = models.ImageField(upload_to='vouchers_qr/', blank=True, null=True, verbose_name="Code QR")
    
    # Statut du retrait
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('picked_up', 'Retiré'),
        ('cancelled', 'Annulé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    picked_up_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de retrait")
    picked_up_by = models.CharField(max_length=255, blank=True, verbose_name="Retiré par")
    
    # Validité
    valid_until = models.DateTimeField(verbose_name="Valide jusqu'au")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Bon #{self.voucher_number} - {self.order.full_name}"
    
    def _build_voucher_number(self):
        """Génère un numéro de bon unique : RET-YYYYMMDD-XXXXXX"""
        from django.utils import timezone
        created_at = timezone.localtime(self.created_at or timezone.now())
        return f"RET-{created_at.strftime('%Y%m%d')}-{self.order.pk:06d}"
    
    def save(self, *args, **kwargs):
        if not self.voucher_number:
            self.voucher_number = self._build_voucher_number()
        if not self.pickup_code:
            self.pickup_code = get_random_string(8, allowed_chars='23456789ABCDEFGHJKLMNPQRSTUVWXYZ')
        
        # Définir la validité (7 jours par défaut)
        if not self.valid_until:
            from datetime import timedelta
            self.valid_until = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Bon de retrait"
        verbose_name_plural = "Bons de retrait"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"Notification #{self.pk} -> {self.recipient} / commande #{self.order_id}"

    @property
    def open_url(self):
        return reverse('store:admin_notification_open', args=[self.pk])

    def mark_as_read(self, commit=True):
        if self.is_read:
            return

        self.is_read = True
        self.read_at = timezone.now()
        if commit:
            self.save(update_fields=['is_read', 'read_at'])


# ============================================
# WEBSITE CONTENT MODELS
# ============================================

class HeroSection(models.Model):
    """
    Main Hero Section content (Singleton-ish: we'll use the first active one or just one record)
    """
    title = models.CharField(max_length=200, default="L'élégance redéfinie")
    subtitle = models.TextField(default="Découvrez notre nouvelle collection de bijoux artisanaux, conçus pour sublimer chaque instant de votre vie.")
    image = models.ImageField(upload_to='hero/', null=True, blank=True)
    button_text = models.CharField(max_length=50, default="Découvrir la collection")
    button_link = models.CharField(max_length=200, default="#catalogue")
    
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            # Ensure only one is active if we want strict singleton, 
            # or just rely on views getting the first()
            pass 
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Section Hero (Bannière)"
        verbose_name_plural = "Sections Hero"


class HeroCard(models.Model):
    """
    Cards displayed below the main hero (Hero Grid)
    """
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200)
    image = models.ImageField(upload_to='hero_cards/')
    link_text = models.CharField(max_length=50, default="Explorer")
    link_url = models.CharField(max_length=200, default="#")
    order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']
        verbose_name = "Carte Hero"
        verbose_name_plural = "Cartes Hero"


class AboutSection(models.Model):
    """
    About Us section content
    """
    title = models.CharField(max_length=200, default="L'excellence depuis 1985")
    paragraph1 = models.TextField(verbose_name="Paragraphe 1")
    paragraph2 = models.TextField(verbose_name="Paragraphe 2", blank=True)
    image = models.ImageField(upload_to='about/')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Section A Propos"
        verbose_name_plural = "Section A Propos"


class AboutStat(models.Model):
    """
    Statistics displayed in the About section
    """
    value = models.CharField(max_length=50, help_text="Ex: 38+")
    label = models.CharField(max_length=100, help_text="Ex: Années d'expérience")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.value} - {self.label}"

    class Meta:
        ordering = ['order']
        verbose_name = "Statistique A Propos"
        verbose_name_plural = "Statistiques A Propos"


# ============================================
# TRUST & FOOTER MODELS
# ============================================

class TrustSignal(models.Model):
    """
    Trust signals like "Free Delivery", "Secure Payment" displayed on homepage
    """
    svg_content = models.TextField(help_text="Raw SVG content for the icon")
    title = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']
        verbose_name = "Signal de Confiance"
        verbose_name_plural = "Signaux de Confiance"


class FooterConfig(models.Model):
    """
    Global footer configuration (Singleton)
    """
    # Newsletter
    newsletter_title = models.CharField(max_length=100, default="Restez informé")
    newsletter_text = models.TextField(default="Inscrivez-vous pour recevoir nos nouveautés et offres exclusives.")
    
    # Brand Column (1)
    company_description = models.TextField(default="L'excellence artisanale depuis 2024.")
    
    # Contact Column (4)
    address = models.TextField(default="Route des huileries\nN° 160, Av. Usoke, C/Lingwala")
    phone = models.CharField(max_length=50, default="+243 97 67 977 48")
    email = models.EmailField(default="info@mkaribu.com")
    
    # Bottom
    copyright_text = models.CharField(max_length=200, default="© 2024 Mkaribu Store. Tous droits réservés.")

    def save(self, *args, **kwargs):
        # Enforce singleton
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Configuration Footer"

    class Meta:
        verbose_name = "Configuration Footer"
        verbose_name_plural = "Configuration Footer"


class SocialLink(models.Model):
    """
    Social media links in the footer
    """
    name = models.CharField(max_length=50, help_text="e.g. Facebook")
    url = models.URLField()
    icon_class = models.CharField(max_length=50, help_text="Bootstrap icon class e.g. 'bi bi-facebook'")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']
        verbose_name = "Lien Social"
        verbose_name_plural = "Liens Sociaux"


class FooterLink(models.Model):
    """
    Links in footer columns
    """
    SECTION_CHOICES = [
        ('help', 'Aide'),
        ('legal', 'Légal'),
        ('boutique', 'Boutique (Optionnel)'),
    ]
    
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=200, help_text="URL absolute or Django named URL")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.get_section_display()})"

    class Meta:
        ordering = ['section', 'order']
        verbose_name = "Lien Footer"
        verbose_name_plural = "Liens Footer"


class Universe(models.Model):
    """
    Category Navigator items (Universes) displayed on the home page.
    """
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='universes/')
    category = models.ForeignKey('products.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='universes')
    identifier = models.CharField(max_length=50, unique=True, help_text="Internal ID for JS filtering (e.g., 'BIJOUX SIMPLES'). Do not change unless you update the code.")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


    class Meta:
        ordering = ['order']
        verbose_name = "Univers (Navigateur)"
        verbose_name_plural = "Univers (Navigateur)"


class Collection(models.Model):
    """
    Curated Collections displayed on the home page (e.g., 'Nos Collections').
    Each collection is linked to a specific product Category.
    """
    title = models.CharField(max_length=100, blank=True, help_text="Optional. If empty, uses the Category name.")
    subtitle = models.CharField(max_length=100, blank=True, help_text="e.g. 'Élégance intemporelle'")
    category = models.ForeignKey('products.Category', on_delete=models.CASCADE, related_name='collections')
    image = models.ImageField(upload_to='collections/', help_text="Image spécifique pour la carte collection (haute qualité)")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title if self.title else self.category.name

    def save(self, *args, **kwargs):
        if not self.title and self.category:
            self.title = self.category.name
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order']
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
