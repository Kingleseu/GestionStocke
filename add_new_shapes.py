
import os
import django
import shutil
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizableComponent

BRAIN_DIR = r"C:\Users\ebenn\.gemini\antigravity\brain\1a670f36-802c-4aa7-927a-13ddca681fab"
MEDIA_ROOT = r"c:\Users\ebenn\Pictures\GestionStocke\media"
COMPONENTS_DIR = os.path.join(MEDIA_ROOT, "customization", "components")

# Ensure directory exists
os.makedirs(COMPONENTS_DIR, exist_ok=True)

print("="*60)
print("➕ AJOUT DES NOUVELLES FORMES")
print("="*60)

# 1. Define New Components
new_components = [
    {
        "name": "Medallion Dog Tag", 
        "component_type": "medallion", 
        "shape_identifier": "dogtag",
        "image_source": "medallion_dogtag_1768436512467.png"  # Generated
    },
    {
        "name": "Medallion Curved Bar", 
        "component_type": "medallion", 
        "shape_identifier": "bar_curved",
        "image_source": "medallion_bar_curved_1768436526457.png"  # Generated
    },
    {
        "name": "Medallion Africa", 
        "component_type": "medallion", 
        "shape_identifier": "africa",
        "image_source": "medallion_round_1768337916270.png" # Placeholder (Quota limit)
    },
    {
        "name": "Medallion Cross", 
        "component_type": "medallion", 
        "shape_identifier": "cross",
        "image_source": "medallion_star_1768337899692.png" # Placeholder (Quota limit)
    },
]

# 2. Process Each
for item in new_components:
    print(f"\nProcessing {item['name']}...")
    
    # 2a. Copy Image
    src_path = os.path.join(BRAIN_DIR, item['image_source'])
    dest_filename = f"medallion_{item['shape_identifier']}.png"
    dest_path = os.path.join(COMPONENTS_DIR, dest_filename)
    
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"  ✅ Image copied to: {dest_filename}")
    else:
        print(f"  ⚠️ Source image missing: {item['image_source']}")
        # Fallback: maintain flow
        
    # 2b. Update/Create DB Record
    # Image path relative to MEDIA_ROOT
    db_image_path = f"customization/components/{dest_filename}"
    
    comp, created = CustomizableComponent.objects.get_or_create(
        name=item['name'],
        defaults={
            "component_type": item['component_type'],
            "shape_identifier": item['shape_identifier'],
            "image": db_image_path
        }
    )
    
    if not created:
        comp.shape_identifier = item['shape_identifier']
        comp.image = db_image_path
        comp.save()
        print(f"  🔄 Updated existing record.")
    else:
        print(f"  ✨ Created new record.")

print("\n" + "="*60)
print("✅ OPÉRATION TERMINÉE")
print("="*60)
print("Note: Les formes 'Africa' et 'Cross' utilisent des images temporaires")
print("en raison des limites de génération. Vous pourrez les remplacer via l'admin.")
