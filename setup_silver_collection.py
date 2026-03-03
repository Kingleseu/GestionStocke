
import os
import shutil
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizableComponent

BRAIN_DIR = r"C:\Users\ebenn\.gemini\antigravity\brain\1a670f36-802c-4aa7-927a-13ddca681fab"
MEDIA_ROOT = r"c:\Users\ebenn\Pictures\GestionStocke\media"
COMPONENTS_DIR = os.path.join(MEDIA_ROOT, "customization", "components")

print("="*60)
print("💎 INSTALLATION DE LA COLLECTION ARGENT (SILVER)")
print("="*60)

# Mappings: (DB_ID, NAME, GENERATED_FILE)
# Note: 'bar_straight' will reuse the 'bar_straight' slot or 'medallion_bar' if we want. 
# Let's standardize IDs.
updates = [
    # NEW SHAPES (Silver)
    {"id": "dogtag", "name": "Medallion Dog Tag", "src": "medallion_dogtag_silver_1768484354629.png"},
    {"id": "bar_curved", "name": "Medallion Curved Bar", "src": "medallion_bar_curved_silver_1768484396085.png"},
    {"id": "bar_straight", "name": "Medallion Bar", "src": "medallion_bar_straight_silver_1768484446276.png"},
    {"id": "africa", "name": "Medallion Africa", "src": "medallion_africa_silver_1768484410978.png"},
    {"id": "cross", "name": "Medallion Cross", "src": "medallion_cross_silver_1768484430783.png"},
    
    # OLD SHAPES (Updated to Silver)
    {"id": "heart", "name": "Medallion Heart", "src": "medallion_heart_silver_1768484492409.png"},
]

for item in updates:
    print(f"\nProcessing {item['name']}...")
    
    # 1. Copy Image
    src_path = os.path.join(BRAIN_DIR, item['src'])
    dest_filename = f"medallion_{item['id']}_silver.png"
    dest_path = os.path.join(COMPONENTS_DIR, dest_filename)
    
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"  ✅ Image copiée: {dest_filename}")
    else:
        print(f"  ❌ Image source manquante: {item['src']}")
        continue

    # 2. Update DB
    db_image_path = f"customization/components/{dest_filename}"
    
    comp, created = CustomizableComponent.objects.get_or_create(
        shape_identifier=item['id'],
        defaults={
            "name": item['name'],
            "component_type": "medallion",
            "image": db_image_path,
            "is_active": True
        }
    )
    
    comp.name = item['name']
    comp.image = db_image_path
    comp.is_active = True
    comp.save()
    print(f"  ✨ Base de données mise à jour.")

print("\n" + "="*60)
print("✅ COLLECTION ARGENT PARTIELLE INSTALLÉE")
print("="*60)
