import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizationFont, ProductCustomizationConfig

def update_fonts():
    print("--- Mise à jour des polices de personnalisation ---")

    # 1. Définir toutes les polices (Mélange Google et Myriad locale)
    all_fonts_data = [
        # Google Fonts (élégantes / luxe)
        {"name": "Dancing Script", "family": "Dancing Script"},
        {"name": "Great Vibes", "family": "Great Vibes"},
        {"name": "Playfair Display", "family": "Playfair Display"},
        {"name": "Cinzel", "family": "Cinzel"},
        {"name": "Cinzel Decorative", "family": "Cinzel Decorative"},
        {"name": "Montserrat", "family": "Montserrat"},
        {"name": "Bodoni Moda", "family": "Bodoni Moda"},
        {"name": "Lora", "family": "Lora"},
        {"name": "Italianno", "family": "Italianno"},
        {"name": "Parisienne", "family": "Parisienne"},
        {"name": "Arial", "family": "Arial"},
        {"name": "Courier New", "family": "Courier New"},
        
        # Myriad Pro (Locales)
        {"name": "Myriad Pro Regular", "family": "Myriad Pro Regular"},
        {"name": "Myriad Pro Bold", "family": "Myriad Pro Bold"},
        {"name": "Myriad Pro Semibold", "family": "Myriad Pro Semibold"},
        {"name": "Myriad Pro Light", "family": "Myriad Pro Light"},
        {"name": "Myriad Pro Italic", "family": "Myriad Pro Italic"},
    ]
    
    established_fonts = []
    for data in all_fonts_data:
        f, created = CustomizationFont.objects.update_or_create(
            name=data['name'],
            defaults={'font_family': data['family'], 'is_active': True}
        )
        established_fonts.append(f)
        status = "Créée" if created else "Mise à jour"
        print(f"[{status}] {f.name} -> family: {f.font_family}")

    # 2. Lier ces polices à TOUTES les configurations Atelier existantes
    configs = ProductCustomizationConfig.objects.all()
    for config in configs:
        config.allowed_fonts.set(established_fonts)
        print(f"[OK] Polices appliquées au produit : {config.product.name}")

    if not configs.exists():
        print("[!] Aucune configuration Atelier trouvée à mettre à jour.")

if __name__ == "__main__":
    update_fonts()
