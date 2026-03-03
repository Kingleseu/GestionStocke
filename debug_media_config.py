
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionStocke.settings')
django.setup()

from products.models import CustomizableComponent

print("="*60)
print("DIAGNOSTIC COMPLET DES IMAGES")
print("="*60)

# 1. Check Settings
print(f"\n1. SETTINGS DJANGO")
print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Non défini')}")
print(f"MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'Non défini')}")
print(f"DEBUG: {getattr(settings, 'DEBUG', 'Non défini')}")

# 2. Check Database Records
print(f"\n2. ENREGISTREMENTS BASE DE DONNÉES")
components = CustomizableComponent.objects.all()
if not components.exists():
    print("❌ Auncun composant trouvé dans la base de données!")
else:
    for comp in components:
        print(f"ID: {comp.id} | Nom: {comp.name}")
        print(f"   ► Champ image (DB): '{comp.image}'")
        
        if comp.image:
            try:
                print(f"   ► URL générée: {comp.image.url}")
                print(f"   ► Chemin absolu: {comp.image.path}")
                exists = os.path.exists(comp.image.path)
                print(f"   ► Fichier existe sur disque? {'✅ OUI' if exists else '❌ NON'}")
            except Exception as e:
                print(f"   ► ERREUR lors de l'accès aux propriétés de l'image: {e}")
        else:
            print("   ► Pas d'image associée")
        print("-" * 30)

# 3. Check Directory Structure
print(f"\n3. STRUCTURE DOSSIER MEDIA")
media_root = settings.MEDIA_ROOT
target_dir = os.path.join(media_root, 'customization', 'components')
print(f"Dossier cible: {target_dir}")
if os.path.exists(target_dir):
    print(f"Contenu du dossier:")
    try:
        for f in os.listdir(target_dir):
            print(f"  - {f}")
    except Exception as e:
        print(f"  Erreur lecture dossier: {e}")
else:
    print("❌ Le dossier 'customization/components' n'existe pas dans MEDIA_ROOT!")

print("\n" + "="*60)
