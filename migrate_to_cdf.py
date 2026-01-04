import os
import django
from decimal import Decimal

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import Product
from accounts.models import Shop
from sales.models import Sale, SaleItem
from purchases.models import Purchase, PurchaseItem

THRESHOLD = Decimal('1000.00')

def migrate_model_prices(model_class, fields, rate, name):
    count = 0
    items = model_class.objects.all()
    for item in items:
        updated = False
        for field in fields:
            val = getattr(item, field)
            if val and val < THRESHOLD:
                setattr(item, field, val * rate)
                updated = True
        if updated:
            item.save()
            count += 1
    if count > 0:
        print(f"  - {name}: {count} records updated.")
    return count

def migrate_all_to_cdf():
    print("--- Démarrage de la migration UNIVERSELLE des prix vers le CDF ---")
    
    shop = Shop.objects.first()
    if not shop:
        print("Erreur: Aucune boutique trouvée.")
        return
        
    rate = shop.usd_to_cdf_rate
    if not rate or rate <= 1:
        print(f"Erreur: Taux invalide ({rate}).")
        return
        
    print(f"Taux utilisé: {rate} CDF/USD")
    print(f"Seuil de détection: < {THRESHOLD}")

    # 1. Product
    migrate_model_prices(Product, ['purchase_price', 'selling_price'], rate, "Produits")
    
    # 2. Sales
    migrate_model_prices(Sale, ['total'], rate, "Ventes")
    migrate_model_prices(SaleItem, ['unit_price', 'subtotal'], rate, "Lignes de vente")
    
    # 3. Purchases
    migrate_model_prices(Purchase, ['total'], rate, "Achats")
    migrate_model_prices(PurchaseItem, ['purchase_price', 'subtotal'], rate, "Lignes d'achat")
    
    print(f"--- Migration terminée ---")

if __name__ == "__main__":
    migrate_all_to_cdf()
