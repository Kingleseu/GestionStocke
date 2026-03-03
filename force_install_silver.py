
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
print("🔨 FORCE INSTALL SILVER COLLECTION")
print("="*60)

# (Source Name in Brain, Destination Filename, Shape Identifier, Display Name)
mappings = [
    ("medallion_dogtag_silver_1768484354629.png", "medallion_dogtag.png", "dogtag", "Medallion Dog Tag"),
    ("medallion_bar_curved_silver_1768484396085.png", "medallion_bar_curved.png", "bar_curved", "Medallion Curved Bar"),
    ("medallion_bar_straight_silver_1768484446276.png", "medallion_bar.png", "bar_straight", "Medallion Bar"),
    ("medallion_africa_silver_1768484410978.png", "medallion_africa.png", "africa", "Medallion Africa"),
    ("medallion_cross_silver_1768484430783.png", "medallion_cross.png", "cross", "Medallion Cross"),
    ("medallion_heart_silver_1768484492409.png", "medallion_heart.png", "heart", "Medallion Heart"),
]

for src_file, dest_file, shape_id, name in mappings:
    print(f"\nProcessing {name} ({shape_id})...")
    
    # 1. Copy File
    src_path = os.path.join(BRAIN_DIR, src_file)
    dest_path = os.path.join(COMPONENTS_DIR, dest_file)
    
    if os.path.exists(src_path):
        try:
            shutil.copy2(src_path, dest_path)
            print(f"  ✅ FILE COPIED: {dest_file}")
        except Exception as e:
            print(f"  ❌ COPY FAILED: {e}")
    else:
        print(f"  ⚠️ SOURCE MISSING: {src_path}")
        
    # 2. Update DB
    try:
        db_image_path = f"customization/components/{dest_file}"
        
        comp, created = CustomizableComponent.objects.get_or_create(
            shape_identifier=shape_id,
            defaults={
                "name": name,
                "component_type": "medallion",
                "image": db_image_path,
                "is_active": True
            }
        )
        
        # Force update fields
        comp.name = name
        comp.image = db_image_path
        comp.component_type = "medallion"
        comp.is_active = True
        comp.save()
        print(f"  ✅ DB UPDATED: {name}")
        
    except Exception as e:
        print(f"  ❌ DB ERROR: {e}")

print("\n" + "="*60)
print("✅ DONE")
