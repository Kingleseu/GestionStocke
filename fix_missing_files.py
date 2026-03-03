
import os
import shutil

BRAIN_DIR = r"C:\Users\ebenn\.gemini\antigravity\brain\1a670f36-802c-4aa7-927a-13ddca681fab"
MEDIA_ROOT = r"c:\Users\ebenn\Pictures\GestionStocke\media"
COMPONENTS_DIR = os.path.join(MEDIA_ROOT, "customization", "components")

print(f"Fixing files in: {COMPONENTS_DIR}")

# 1. generated images (REAL)
real_images = [
    ("medallion_dogtag_1768436512467.png", "medallion_dogtag.png"),
    ("medallion_bar_curved_1768436526457.png", "medallion_bar_curved.png")
]

for src_name, dest_name in real_images:
    src = os.path.join(BRAIN_DIR, src_name)
    dest = os.path.join(COMPONENTS_DIR, dest_name)
    if os.path.exists(src):
        shutil.copy2(src, dest)
        print(f"✅ Restored {dest_name}")
    else:
        print(f"❌ Source missing for {dest_name}: {src}")

# 2. Placeholders (Reset to safe defaults)
# Africa -> Round
# Cross -> Star
placeholders = [
    ("medallion_round_1768337916270.png", "medallion_africa.png"),
    ("medallion_star_1768337899692.png", "medallion_cross.png")
]

for src_name, dest_name in placeholders:
    src = os.path.join(BRAIN_DIR, src_name)
    dest = os.path.join(COMPONENTS_DIR, dest_name)
    # Always overwrite to ensure valid image
    if os.path.exists(src):
        shutil.copy2(src, dest)
        print(f"⚠️  Reset placeholder {dest_name}")

print("File fix complete.")
