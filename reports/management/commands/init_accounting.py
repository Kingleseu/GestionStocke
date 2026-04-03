from django.core.management.base import BaseCommand
from accounts.models import Shop
from reports.models import ExpenseCategory

class Command(BaseCommand):
    help = 'Initialise les catégories de dépenses par défaut pour toutes les boutiques.'

    def handle(self, *args, **options):
        categories = [
            ('Loyer', 'bi-house'),
            ('Salaires', 'bi-people'),
            ('Électricité', 'bi-lightning'),
            ('Eau', 'bi-droplet'),
            ('Transport', 'bi-truck'),
            ('Marketing', 'bi-megaphone'),
            ('Maintenance', 'bi-tools'),
            ('Divers', 'bi-patch-question'),
        ]
        
        shops = Shop.objects.all()
        if not shops.exists():
            self.stdout.write(self.style.WARNING("Aucune boutique trouvée."))
            return

        for shop in shops:
            self.stdout.write(f"Initialisation pour {shop.name}...")
            for name, icon in categories:
                obj, created = ExpenseCategory.objects.get_or_create(
                    shop=shop,
                    name=name,
                    defaults={'icon': icon}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"  + Catégorie '{name}' créée."))
                else:
                    self.stdout.write(f"  - Catégorie '{name}' existe déjà.")
