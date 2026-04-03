from django.db import models
from django.contrib.auth.models import User
from accounts.models import Shop
from decimal import Decimal
from django.core.validators import MinValueValidator

class ExpenseCategory(models.Model):
    """Catégorie de dépenses (Loyer, Salaires, Électricité, etc.)"""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='expense_categories')
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(max_length=50, default='bi-cash', help_text="Nom d'icône Bootstrap")

    class Meta:
        verbose_name = "Catégorie de dépense"
        verbose_name_plural = "Catégories de dépenses"
        unique_together = ['shop', 'name']

    def __str__(self):
        return f"{self.name} ({self.shop.name})"

class Expense(models.Model):
    """Dépense de fonctionnement (frais fixes ou variables)"""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses', verbose_name="Catégorie")
    title = models.CharField(max_length=200, verbose_name="Intitulé")
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant (FC)"
    )
    date = models.DateField(verbose_name="Date de la dépense")
    notes = models.TextField(blank=True, verbose_name="Notes / Justificatif")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Enregistré par")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount} FC ({self.date})"
