from django.db import models
from django.conf import settings
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
    
    def total_price(self):
        return self.product.selling_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class WebOrder(models.Model):
    """
    A completed order placed via the website.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PAID', 'Payé'),
        ('SHIPPED', 'Expédié'),
        ('DELIVERED', 'Livré'),
        ('CANCELLED', 'Annulé'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"

class WebOrderItem(models.Model):
    order = models.ForeignKey(WebOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


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
