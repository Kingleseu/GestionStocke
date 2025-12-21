# accounts/management/commands/setup_groups.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from products.models import Product, Category
from purchases.models import Purchase, PurchaseItem
from sales.models import Sale, SaleItem


class Command(BaseCommand):
    help = 'Crée les groupes Manager et Cashier avec leurs permissions'

    def handle(self, *args, **kwargs):
        # Créer le groupe Manager
        manager_group, created = Group.objects.get_or_create(name='Manager')
        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Groupe "Manager" cree'))
        else:
            self.stdout.write(self.style.WARNING('[INFO] Groupe "Manager" existe deja'))

        # Créer le groupe Cashier
        cashier_group, created = Group.objects.get_or_create(name='Cashier')
        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Groupe "Cashier" cree'))
        else:
            self.stdout.write(self.style.WARNING('[INFO] Groupe "Cashier" existe deja'))

        # Permissions pour Manager (accès total)
        manager_permissions = Permission.objects.filter(
            content_type__in=ContentType.objects.filter(
                app_label__in=['products', 'purchases', 'sales', 'inventory', 'reports']
            )
        )
        manager_group.permissions.set(manager_permissions)
        self.stdout.write(self.style.SUCCESS(f'[OK] {manager_permissions.count()} permissions ajoutees au groupe Manager'))

        # Permissions pour Cashier (uniquement ventes)
        cashier_permissions = Permission.objects.filter(
            content_type__in=ContentType.objects.filter(
                app_label='sales',
                model__in=['sale', 'saleitem']
            )
        )
        # Ajouter aussi la permission de voir les produits (mais pas les modifier)
        product_view_perm = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Product),
            codename='view_product'
        )
        cashier_permissions = list(cashier_permissions) + list(product_view_perm)
        cashier_group.permissions.set(cashier_permissions)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(cashier_permissions)} permissions ajoutees au groupe Cashier'))

        self.stdout.write(self.style.SUCCESS('\n=== Configuration des groupes terminee ! ==='))
        self.stdout.write(self.style.SUCCESS('\nResume :'))
        self.stdout.write(f'  - Manager : Acces complet (produits, achats, ventes, rapports)')
        self.stdout.write(f'  - Cashier : Acces caisse uniquement (ventes + consultation produits)')

