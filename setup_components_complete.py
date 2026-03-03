"""
Script complet pour configurer les images des composants de personnalisation
"""
import os
import django
import shutil

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizableComponent

# Chemins
BRAIN_DIR = r"C:\Users\ebenn\.gemini\antigravity\brain\1a670f36-802c-4aa7-927a-13ddca681fab"
MEDIA_ROOT = r"c:\Users\ebenn\Pictures\GestionStocke\media"
COMPONENTS_DIR = os.path.join(MEDIA_ROOT, "customization", "components")

# Créer le répertoire si nécessaire
os.makedirs(COMPONENTS_DIR, exist_ok=True)

print("=" * 60)
print("🔧 CONFIGURATION DES COMPOSANTS DE PERSONNALISATION")
print("=" * 60)

# Étape 1: Vérifier/Créer les composants
print("\n📋 Étape 1: Vérification des composants...")
components_data = [
    {"name": "Medallion Heart", "component_type": "medallion", "shape_identifier": "heart"},
    {"name": "Medallion Clover", "component_type": "medallion", "shape_identifier": "clover"},
    {"name": "Medallion Star", "component_type": "medallion", "shape_identifier": "star"},
    {"name": "Medallion Round", "component_type": "medallion", "shape_identifier": "round"},
]

for comp_data in components_data:
    comp, created = CustomizableComponent.objects.get_or_create(
        name=comp_data["name"],
        defaults=comp_data
    )
    if created:
        print(f"  ✅ Créé: {comp.name}")
    else:
        print(f"  ℹ️  Existe déjà: {comp.name}")

# Étape 2: Copier les images
print("\n📁 Étape 2: Copie des images...")
image_mapping = {
    "medallion_heart.png": "medallion_heart_1768337866975.png",
    "medallion_clover.png": "medallion_clover_1768337883097.png",
    "medallion_star.png": "medallion_star_1768337899692.png",
    "medallion_round.png": "medallion_round_1768337916270.png",
}

for dest_name, source_name in image_mapping.items():
    source_path = os.path.join(BRAIN_DIR, source_name)
    dest_path = os.path.join(COMPONENTS_DIR, dest_name)
    
    if os.path.exists(source_path):
        shutil.copy2(source_path, dest_path)
        print(f"  ✅ Copié: {dest_name}")
    else:
        print(f"  ⚠️  Source non trouvée: {source_name}")

# Étape 3: Associer les images aux composants
print("\n🔗 Étape 3: Association des images aux composants...")
updates = [
    ("Heart", "customization/components/medallion_heart.png"),
    ("Clover", "customization/components/medallion_clover.png"),
    ("Star", "customization/components/medallion_star.png"),
    ("Round", "customization/components/medallion_round.png"),
]

for name_part, image_path in updates:
    try:
        component = CustomizableComponent.objects.filter(name__icontains=name_part).first()
        
        if component:
            component.image = image_path
            component.save()
            print(f"  ✅ {component.name}: {image_path}")
        else:
            print(f"  ⚠️  Composant non trouvé: {name_part}")
    except Exception as e:
        print(f"  ❌ Erreur pour {name_part}: {e}")

# Étape 4: Rapport final
print("\n" + "=" * 60)
print("📊 RAPPORT FINAL")
print("=" * 60)

all_components = CustomizableComponent.objects.all()
print(f"\nTotal de composants: {all_components.count()}\n")

for comp in all_components:
    status = "✅" if comp.image else "❌"
    image_info = comp.image.name if comp.image else "PAS D IMAGE"
    print(f"{status} {comp.name}")
    print(f"   Type: {comp.component_type}")
    print(f"   Image: {image_info}")
    print(f"   Actif: {'Oui' if comp.is_active else 'Non'}")
    print()

print("=" * 60)
print("✨ CONFIGURATION TERMINÉE!")
print("=" * 60)
print("\n💡 Prochaines étapes:")
print("  1. Actualisez la page de création de produit")
print("  2. Activez 'Personnalisation' sur un produit")
print("  3. Vérifiez que les images des formes s'affichent")
