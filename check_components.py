import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionStocke.settings')
django.setup()

from products.models import CustomizableComponent

# Vérifier les composants existants
components = CustomizableComponent.objects.all()
print(f"📊 Composants existants: {components.count()}\n")

for comp in components:
    print(f"  - {comp.name} (Type: {comp.component_type}, Image: {bool(comp.image)})")

# Si aucun composant n'existe, en créer
if components.count() == 0:
    print("\n🔧 Création des composants de base...\n")
    
    default_components = [
        {"name": "Medallion Heart", "component_type": "medallion", "shape_identifier": "heart"},
        {"name": "Medallion Clover", "component_type": "medallion", "shape_identifier": "clover"},
        {"name": "Medallion Star", "component_type": "medallion", "shape_identifier": "star"},
        {"name": "Medallion Round", "component_type": "medallion", "shape_identifier": "round"},
    ]
    
    for comp_data in default_components:
        comp = CustomizableComponent.objects.create(**comp_data)
        print(f"  ✅ Créé: {comp.name}")

print("\n✨ Terminé!")
