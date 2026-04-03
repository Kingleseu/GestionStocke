from datetime import timedelta
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


ACCOUNT_SPACE_CUSTOMER = 'customer'
ACCOUNT_SPACE_STAFF = 'staff'
ACCOUNT_SPACE_CHOICES = [
    (ACCOUNT_SPACE_CUSTOMER, 'Compte client boutique'),
    (ACCOUNT_SPACE_STAFF, 'Compte personnel boutique'),
]

STAFF_ROLE_MANAGER = 'Manager'
STAFF_ROLE_CASHIER = 'Cashier'
STAFF_ROLE_CHOICES = [
    (STAFF_ROLE_MANAGER, 'Manager'),
    (STAFF_ROLE_CASHIER, 'Caissier'),
]

OTP_PURPOSE_LOGIN = 'login'
OTP_PURPOSE_CHOICES = [
    (OTP_PURPOSE_LOGIN, 'Connexion'),
]


def default_invitation_expiry():
    return timezone.now() + timedelta(days=7)


class CashierInvitation(models.Model):
    """Invitation du personnel. Le nom du modele est garde pour la compatibilite."""

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_invitations')
    used_by = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitation_used',
    )
    email = models.EmailField()
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=STAFF_ROLE_CHOICES, default=STAFF_ROLE_CASHIER)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_invitation_expiry)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Invitation du personnel'
        verbose_name_plural = 'Invitations du personnel'

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def __str__(self):
        return f'Invitation {self.get_role_display()} pour {self.email}'


class Shop(models.Model):
    """Boutique/Magasin appartenant a un manager."""

    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_shops')
    created_at = models.DateTimeField(auto_now_add=True)

    address = models.TextField(blank=True, null=True, verbose_name='Adresse')
    rccm = models.CharField(max_length=100, blank=True, null=True, verbose_name='RCCM')
    id_nat = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID.NAT')
    nif = models.CharField(max_length=100, blank=True, null=True, verbose_name='NIF')
    bureau = models.CharField(max_length=100, blank=True, null=True, verbose_name='Bureau')
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telephone')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')

    usd_to_cdf_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2800.00,
        verbose_name='Taux de conversion FC',
    )
    vat_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=16.00,
        verbose_name='Pourcentage TVA (%)',
    )

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Profil utilisateur partage pour le personnel et l'administration."""

    CURRENCY_CHOICES = [
        ('FC', 'Franc Congolais (FC)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='FC')
    phone = models.CharField(max_length=50, blank=True, verbose_name='Telephone')
    employee_code = models.CharField(max_length=50, blank=True, verbose_name='Matricule')
    position_title = models.CharField(max_length=100, blank=True, verbose_name='Poste')
    address = models.TextField(blank=True, verbose_name='Adresse')
    hire_date = models.DateField(null=True, blank=True, verbose_name="Date d'embauche")
    emergency_contact_name = models.CharField(max_length=150, blank=True, verbose_name="Nom du contact d'urgence")
    emergency_contact_phone = models.CharField(max_length=50, blank=True, verbose_name="Telephone du contact d'urgence")
    notes = models.TextField(blank=True, verbose_name='Notes internes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profil de {self.user.username}'


class UserActivity(models.Model):
    """Historique des connexions et deconnexions."""

    ACTIVITY_TYPES = [
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Deconnexion'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activite utilisateur'
        verbose_name_plural = 'Activites utilisateurs'

    def __str__(self):
        return f'{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}'


class EmailOTP(models.Model):
    """Code OTP email pour la connexion sans mot de passe."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    email = models.EmailField()
    purpose = models.CharField(max_length=20, choices=OTP_PURPOSE_CHOICES, default=OTP_PURPOSE_LOGIN)
    account_space = models.CharField(max_length=20, choices=ACCOUNT_SPACE_CHOICES)
    code_hash = models.CharField(max_length=128)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Code OTP email'
        verbose_name_plural = 'Codes OTP email'
        indexes = [
            models.Index(fields=['email', 'account_space', 'purpose']),
            models.Index(fields=['user', 'purpose', 'created_at']),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_available(self):
        return self.consumed_at is None and not self.is_expired

    def mark_consumed(self, commit=True):
        if self.consumed_at is None:
            self.consumed_at = timezone.now()
            if commit:
                self.save(update_fields=['consumed_at'])

    def __str__(self):
        return f'OTP {self.email} ({self.account_space})'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return

    profile = UserProfile.objects.create(user=instance)

    if instance.is_superuser:
        shop, _ = Shop.objects.get_or_create(name='Boutique Principale (Admin)', created_by=instance)
        profile.shop = shop
        profile.save(update_fields=['shop'])


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=instance)
        if instance.is_superuser:
            shop, _ = Shop.objects.get_or_create(name='Boutique Principale (Admin)', created_by=instance)
            profile.shop = shop
            profile.save(update_fields=['shop'])
