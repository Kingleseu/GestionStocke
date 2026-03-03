
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

print("="*60)
print("➕ INSTALLATION DES FORMES SUPPLÉMENTAIRES")
print("="*60)

# Mappings (Source in Brain -> Dest in Media)
# Note: For Africa/Cross we use existing generated images as placeholders
commands = [
    {
        "name": "Medallion Dog Tag",
        "type": "medallion",
        "id": "dogtag",
        "src": "medallion_dogtag_1768436512467.png"
    },
    {
        "name": "Medallion Curved Bar",
        "type": "medallion",
        "id": "bar_curved",
        "src": "medallion_bar_curved_1768436526457.png"
    },
    {
        "name": "Medallion Africa",
        "type": "medallion",
        "id": "africa",
        "src": "medallion_round_1768337916270.png" # Placeholder
    },
    {
        "name": "Medallion Cross",
        "type": "medallion",
        "id": "cross",
        "src": "medallion_star_1768337899692.png" # Placeholder
    }
]

for cmd in commands:
    print(f"\nProcessing {cmd['name']}...")
    
    # 1. Copy File
    src_path = os.path.join(BRAIN_DIR, cmd['src'])
    dest_filename = f"medallion_{cmd['id']}.png"
    dest_path = os.path.join(COMPONENTS_DIR, dest_filename)
    
    # If source exists in brain, use it. 
    # If not, check if we already have it in destination (maybe manual upload)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"  ✅ Image copiée: {dest_filename}")
    elif os.path.exists(dest_path):
        print(f"  ℹ️  Image déjà présente dans media: {dest_filename}")
    else:
        print(f"  ⚠️  Image source manquante: {cmd['src']}")
        
    # 2. Update DB
    db_image_path = f"customization/components/{dest_filename}"
    
    comp, created = CustomizableComponent.objects.get_or_create(
        name=cmd['name'],
        defaults={
            "component_type": cmd['type'],
            "shape_identifier": cmd['id'],
            "image": db_image_path,
            "is_active": True
        }
    )
    
    if not created:
        comp.shape_identifier = cmd['id']
        comp.image = db_image_path
        comp.save()
        print(f"  🔄 Données mises à jour dans la BD.")
    else:
        print(f"  ✨ Nouveau composant créé dans la BD.")

print("\n" + "="*60)
print("✅ TERMINÉ")
print("="*60)
print("Veuillez actualiser le formulaires de création de produit pour voir les nouvelles formes.")
