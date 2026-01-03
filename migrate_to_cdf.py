import os
import django
from decimal import Decimal

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import Product
from accounts.models import Shop

def migrate_prices_to_cdf():
    print("--- Démarrage de la migration des prix vers le CDF ---")
    
    products = Product.objects.all()
    count = 0
    
    for product in products:
        shop = product.shop
        if not shop:
            print(f"Skipping product {product.name} (no shop assigned)")
            continue
            
        rate = shop.usd_to_cdf_rate
        if not rate or rate <= 0:
            print(f"Skipping product {product.name} (invalid shop rate: {rate})")
            continue
            
        # Convert prices
        old_purchase = product.purchase_price
        old_selling = product.selling_price
        
        product.purchase_price = old_purchase * rate
        product.selling_price = old_selling * rate
        product.save()
        
        print(f"Converted: {product.name} | {old_purchase}$ -> {product.purchase_price} FC | {old_selling}$ -> {product.selling_price} FC")
        count += 1
        
    print(f"--- Migration terminée : {count} produits mis à jour ---")

if __name__ == "__main__":
    migrate_prices_to_cdf()
