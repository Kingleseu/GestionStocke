
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

# Ensure directory exists
os.makedirs(COMPONENTS_DIR, exist_ok=True)

print("="*60)
print("🚀 INSTALLATION DES IMAGES FOURNIES PAR L'UTILISATEUR")
print("="*60)

# Map user uploaded keys to database keys
# uploaded_image_0 -> Silver Curved Bar
# uploaded_image_1 -> Silver Cross
# uploaded_image_2 -> Gold Dog Tag
# uploaded_image_3 -> Gold Curved Bar (We'll skip this one for the main slot to avoid conflict, or make a variant?)
# Let's use Silver Curved Bar for 'bar_curved' as it looks cleaner in the preview likely.

mappings = [
    {
        "src": "uploaded_image_0_1768598060571.png", 
        "dest": "medallion_bar_curved.png", 
        "shape_id": "bar_curved", 
        "name": "Medallion Curved Bar"
    },
    {
        "src": "uploaded_image_1_1768598060571.png", 
        "dest": "medallion_cross.png", 
        "shape_id": "cross", 
        "name": "Medallion Cross"
    },
    {
        "src": "uploaded_image_2_1768598060571.png", 
        "dest": "medallion_dogtag.png", 
        "shape_id": "dogtag", 
        "name": "Medallion Dog Tag"
    },
]

for item in mappings:
    print(f"\nProcessing {item['name']}...")
    
    # 1. Copy File
    src_path = os.path.join(BRAIN_DIR, item['src'])
    dest_path = os.path.join(COMPONENTS_DIR, item['dest'])
    
    if os.path.exists(src_path):
        try:
            shutil.copy2(src_path, dest_path)
            print(f"  ✅ IMAGE COPIÉE: {item['dest']}")
        except Exception as e:
            print(f"  ❌ ERREUR COPIE: {e}")
            continue
    else:
        print(f"  ⚠️ IMAGE SOURCE ABSENTE: {src_path}")
        continue
        
    # 2. Update DB
    try:
        db_image_path = f"customization/components/{item['dest']}"
        
        comp, created = CustomizableComponent.objects.get_or_create(
            shape_identifier=item['shape_id'],
            defaults={
                "name": item['name'],
                "component_type": "medallion",
                "image": db_image_path,
                "is_active": True
            }
        )
        
        # Always update to ensure correctness
        comp.name = item['name']
        comp.image = db_image_path
        comp.is_active = True
        comp.save()
        print(f"  ✨ BASE DE DONNÉES MISE À JOUR: {item['name']}")
        
    except Exception as e:
        print(f"  ❌ ERREUR DB: {e}")

print("\n" + "="*60)
print("✅ TERMINÉ")
