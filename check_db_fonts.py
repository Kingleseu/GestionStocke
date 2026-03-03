import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizationFont, ProductCustomizationConfig

def check_fonts():
    fonts = CustomizationFont.objects.all()
    print(f"Total fonts in DB: {fonts.count()}")
    for f in fonts:
        print(f"ID: {f.id}, Name: {f.name}, Family: {f.font_family}, Active: {f.is_active}")
    
    configs = ProductCustomizationConfig.objects.all()
    print(f"\nTotal configs in DB: {configs.count()}")
    for c in configs:
        print(f"Product: {c.product.name}, Allowed Fonts Count: {c.allowed_fonts.count()}")

if __name__ == "__main__":
    check_fonts()
