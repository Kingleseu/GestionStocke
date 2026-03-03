import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import Product, CustomizationFont, CustomizableComponent, ProductCustomizationConfig

def setup_atelier():
    print("--- Atelier Studio Initialisation ---")

    # 1. Create fonts
    fonts_data = [
        {"name": "Dancing Script", "family": "Dancing Script, cursive", "url": "https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap"},
        {"name": "Playfair Display", "family": "Playfair Display, serif", "url": "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap"},
        {"name": "Great Vibes", "family": "Great Vibes, cursive", "url": "https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap"},
        {"name": "Inter", "family": "Inter, sans-serif", "url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"},
    ]
    
    fonts = []
    for data in fonts_data:
        f, created = CustomizationFont.objects.get_or_create(
            name=data['name'],
            defaults={'font_family': data['family'], 'font_url': data['url']}
        )
        fonts.append(f)
        if created: print(f"[OK] Font created: {f.name}")

    # 2. Create components (Medallions)
    components_data = [
        {"name": "Medallion Heart", "shape": "heart", "price": 0.00},
        {"name": "Medallion Clover", "shape": "clover", "price": 2.00},
        {"name": "Medallion Star", "shape": "star", "price": 1.50},
        {"name": "Medallion Round", "shape": "round", "price": 0.00},
    ]
    
    components = []
    for data in components_data:
        c, created = CustomizableComponent.objects.get_or_create(
            name=data['name'],
            defaults={
                'component_type': 'medallion',
                'shape_identifier': data['shape'],
                'base_price_modifier': Decimal(str(data['price']))
            }
        )
        components.append(c)
        if created: print(f"[OK] Component created: {c.name}")

    # 3. Configure test product
    product = Product.objects.filter(is_customizable=True).first()
    if not product:
        product = Product.objects.first()
        if product:
            product.is_customizable = True
            product.save()
    
    if product:
        config, created = ProductCustomizationConfig.objects.get_or_create(product=product)
        config.allowed_fonts.set(fonts)
        config.allowed_components.set(components)
        config.studio_config = {
            "max_length": 12,
            "price_formula": {"base": 5.0, "per_char": 0},
            "preview_config": {"position": {"x": 50, "y": 60}, "size": 30, "color": "#1a1a1a"}
        }
        config.save()
        print(f"[OK] Studio configured for product: {product.name}")
    else:
        print("[ERROR] No product found.")

if __name__ == "__main__":
    setup_atelier()
