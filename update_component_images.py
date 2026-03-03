import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionStocke.settings')
django.setup()

from products.models import CustomizableComponent

# Mapping: nom partiel du composant -> fichier image
updates = [
    ("Heart", "customization/components/medallion_heart.png"),
    ("Clover", "customization/components/medallion_clover.png"),
    ("Star", "customization/components/medallion_star.png"),
    ("Round", "customization/components/medallion_round.png"),
]

print("🔧 Mise à jour des images de composants...\n")

for name_part, image_path in updates:
    try:
        # Trouver le composant
        component = CustomizableComponent.objects.filter(name__icontains=name_part).first()
        
        if component:
            component.image = image_path
            component.save()
            print(f"✅ {component.name}: {image_path}")
        else:
            print(f"⚠️  Aucun composant trouvé contenant '{name_part}'")
    except Exception as e:
        print(f"❌ Erreur pour {name_part}: {e}")

print("\n📊 État final:")
for comp in CustomizableComponent.objects.all():
    status = "✅" if comp.image else "❌"
    print(f"{status} {comp.name}: {comp.image or 'PAS D IMAGE'}")
