import os
import django
import shutil
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionStocke.settings')
django.setup()

from products.models import CustomizableComponent
from django.core.files import File

# Chemins
BRAIN_DIR = r"C:\Users\ebenn\.gemini\antigravity\brain\1a670f36-802c-4aa7-927a-13ddca681fab"
MEDIA_ROOT = r"c:\Users\ebenn\Pictures\GestionStocke\media"
COMPONENTS_DIR = os.path.join(MEDIA_ROOT, "customization", "components")

# Créer le répertoire si nécessaire
os.makedirs(COMPONENTS_DIR, exist_ok=True)

# Mapping des images générées vers les noms de composants
image_mapping = {
    "Medallion Heart": "medallion_heart_1768337866975.png",
    "Medallion Clover": "medallion_clover_1768337883097.png",
    "Medallion Star": "medallion_star_1768337899692.png",
    "Medallion Round": "medallion_round_1768337916270.png",
}

print("🔧 Configuration des images de composants...\n")

for comp_name, image_filename in image_mapping.items():
    try:
        # Trouver le composant dans la base de données
        component = CustomizableComponent.objects.filter(name__icontains=comp_name.split()[-1]).first()
        
        if not component:
            print(f"⚠️  Composant '{comp_name}' non trouvé dans la base de données")
            continue
        
        # Chemin source et destination
        source_path = os.path.join(BRAIN_DIR, image_filename)
        dest_filename = f"{comp_name.lower().replace(' ', '_')}.png"
        dest_path = os.path.join(COMPONENTS_DIR, dest_filename)
        
        if not os.path.exists(source_path):
            print(f"⚠️  Image source non trouvée: {source_path}")
            continue
        
        # Copier l'image
        shutil.copy2(source_path, dest_path)
        
        # Mettre à jour le composant
        relative_path = os.path.join("customization", "components", dest_filename)
        component.image = relative_path
        component.save()
        
        print(f"✅ {component.name}: Image configurée ({dest_filename})")
        
    except Exception as e:
        print(f"❌ Erreur pour {comp_name}: {e}")

print("\n✨ Configuration terminée!")

# Afficher l'état final
print("\n📊 État des composants:")
for comp in CustomizableComponent.objects.all():
    status = "✅" if comp.image else "❌"
    print(f"{status} {comp.name}: {comp.image or 'PAS D\'IMAGE'}")
