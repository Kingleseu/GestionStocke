from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from products.models import Product, Category


class Promotion(models.Model):
    """
    Modèle de gestion des promotions programmables.
    Permet de créer des règles de réduction temporaires et ciblées.
    """
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Pourcentage (%)'),
        ('fixed', 'Montant fixe (€)'),
    ]
    
    SCOPE_CHOICES = [
        ('all_products', 'Tous les produits'),
        ('specific_products', 'Produits sélectionnés'),
        ('specific_categories', 'Catégories sélectionnées'),
    ]
    
    # Identité
    name = models.CharField(
        max_length=100,
        verbose_name="Nom de la promotion",
        help_text="ex: 'Soldes Printemps 2026'"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description détaillée"
    )
    
    # Réduction
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        verbose_name="Type de réduction"
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Valeur de réduction",
        help_text="En pourcentage (0-100) ou montant en €"
    )
    
    # Portée (scope)
    scope = models.CharField(
        max_length=30,
        choices=SCOPE_CHOICES,
        default='all_products',
        verbose_name="Portée de la promotion"
    )
    
    # Produits et catégories (si scope='specific_products' ou 'specific_categories')
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='promotions',
        verbose_name="Produits concernés"
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='promotions',
        verbose_name="Catégories concernées"
    )
    
    # Programmation temporelle
    start_date = models.DateTimeField(
        verbose_name="Date et heure de début"
    )
    end_date = models.DateTimeField(
        verbose_name="Date et heure de fin"
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name="Promotion active",
        help_text="Cochez pour activer manuellement. Utilise start/end_date pour l'automatisation."
    )
    
    # Marketing visuel
    banner_image = models.ImageField(
        upload_to='promotions/banners/',
        blank=True,
        null=True,
        verbose_name="Image de bannière",
        help_text="Affiché en haut de la page pendant la promo"
    )
    banner_message = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Message de la bannière",
        help_text="ex: 'Soldes du Printemps! -20% tout!' ou '🎉 Promotion jusqu'au 15 mars!'"
    )
    display_badge = models.BooleanField(
        default=True,
        verbose_name="Afficher un badge sur les produits"
    )
    badge_custom_text = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Texte du badge personnalisé",
        help_text="Si vide, le système génère automatiquement. ex: '-20% OFF' ou 'SOLDES'"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créée le"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifiée le"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_promotions',
        verbose_name="Créée par"
    )
    
    # Aide pour le calcul
    note_business = models.TextField(
        blank=True,
        verbose_name="Notes internes",
        help_text="Notes pour le gestionnaire (client, raison, etc.)"
    )
    
    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_active']),
        ]
    
    def _format_discount_value(self):
        text = format(self.discount_value.normalize(), 'f')
        if '.' in text:
            text = text.rstrip('0').rstrip('.')
        return text

    def __str__(self):
        symbol = '%' if self.discount_type == 'percentage' else '€'
        return f"{self.name} (-{self._format_discount_value()}{symbol})"
    
    @property
    def is_running(self):
        """Est-ce que la promotion est en cours en ce moment ?"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.is_active
    
    @property
    def is_upcoming(self):
        """La promotion est-elle programmée pour plus tard ?"""
        now = timezone.now()
        return self.start_date > now and self.is_active
    
    @property
    def is_expired(self):
        """La promotion est-elle expirée ?"""
        now = timezone.now()
        return self.end_date < now
    
    @property
    def status(self):
        """Retourne le statut actuel de la promotion"""
        if not self.is_active:
            return 'inactive'
        if self.is_running:
            return 'active'
        if self.is_upcoming:
            return 'upcoming'
        if self.is_expired:
            return 'expired'
        return 'unknown'
    
    def get_badge_text(self):
        """Génère le texte du badge automatiquement"""
        if self.badge_custom_text:
            return self.badge_custom_text
        
        if self.discount_type == 'percentage':
            return f"-{int(self.discount_value)}%"
        else:
            return f"-{self.discount_value}€"
    
    def get_applicable_products(self):
        """Retourne tous les produits concernés par cette promotion"""
        if self.scope == 'all_products':
            return Product.objects.filter(is_active=True)
        elif self.scope == 'specific_products':
            return self.products.all()
        elif self.scope == 'specific_categories':
            return Product.objects.filter(
                category__in=self.categories.all(),
                is_active=True
            )
        return Product.objects.none()
    
    def calculate_discounted_price(self, original_price):
        """
        Calcule le prix réduit en fonction de la réduction.
        
        Args:
            original_price: Le prix original en Decimal
            
        Returns:
            Decimal: Le prix réduit
        """
        original_price = Decimal(str(original_price))
        
        if self.discount_type == 'percentage':
            reduction = original_price * (self.discount_value / 100)
            return original_price - reduction
        else:  # fixed
            return max(Decimal('0.00'), original_price - self.discount_value)
    
    def save(self, *args, **kwargs):
        """Validation avant sauvegarde"""
        # Validation des dates
        if self.start_date >= self.end_date:
            raise ValueError("La date de fin doit être après la date de début")
        
        # Validation de la valeur de réduction
        if self.discount_type == 'percentage':
            if not (0 < self.discount_value <= 100):
                raise ValueError("Le pourcentage doit être entre 0 et 100")
        
        super().save(*args, **kwargs)


class PromotionLog(models.Model):
    """
    Journal d'audit pour les promotions.
    Trace toutes les modifications et changements d'état.
    """
    
    ACTION_CHOICES = [
        ('created', 'Créée'),
        ('updated', 'Modifiée'),
        ('activated', 'Activée'),
        ('deactivated', 'Désactivée'),
        ('started', 'Débuté'),
        ('ended', 'Terminée'),
        ('deleted', 'Supprimée'),
    ]
    
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="Promotion"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage"
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Détails",
        help_text="Détails additionnels en JSON (avant/après, etc.)"
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promotion_logs',
        verbose_name="Effectuée par",
        help_text="L'utilisateur qui a effectué l'action"
    )
    
    class Meta:
        verbose_name = "Journal de promotion"
        verbose_name_plural = "Journaux de promotions"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['promotion', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.promotion.name} - {self.get_action_display()} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"
