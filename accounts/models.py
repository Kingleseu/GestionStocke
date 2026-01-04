from django.db import models
from django.contrib.auth.models import User
import uuid

class CashierInvitation(models.Model):
    """Invitation pour devenir caissier"""
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_invitations')
    used_by = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitation_used')
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Invitation {self.token} par {self.created_by.username}"


class Shop(models.Model):
    """Boutique/Magasin appartenant à un Manager"""
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_shops')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Administrative information
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    rccm = models.CharField(max_length=100, blank=True, null=True, verbose_name="RCCM")
    id_nat = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID.NAT")
    nif = models.CharField(max_length=100, blank=True, null=True, verbose_name="NIF")
    bureau = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bureau")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    
    # Financial settings
    usd_to_cdf_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=2800.00, 
        verbose_name="Taux de conversion FC"
    )
    vat_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=16.00, 
        verbose_name="Pourcentage TVA (%)"
    )
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    """Profil utilisateur avec préférences"""
    CURRENCY_CHOICES = [
        ('FC', 'Franc Congolais (FC)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='FC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profil de {self.user.username}"


class UserActivity(models.Model):
    """Historique d'activité des utilisateurs (connexions, etc.)"""
    ACTIVITY_TYPES = [
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Activité utilisateur"
        verbose_name_plural = "Activités utilisateurs"

# Signaux pour créer automatiquement le profil
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Créer un profil par défaut
        profile = UserProfile.objects.create(user=instance)
        
        # Si c'est un superuser, lui créer une boutique par défaut s'il n'en a pas
        if instance.is_superuser:
            shop, _ = Shop.objects.get_or_create(name="Boutique Principale (Admin)", created_by=instance)
            profile.shop = shop
            profile.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Créer le profil s'il n'existe pas (pour les anciens utilisateurs)
        UserProfile.objects.create(user=instance)
        # Si superuser, attacher shop
        if instance.is_superuser:
            shop, _ = Shop.objects.get_or_create(name="Boutique Principale (Admin)", created_by=instance)
            instance.profile.shop = shop
            instance.profile.save()
        
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"
