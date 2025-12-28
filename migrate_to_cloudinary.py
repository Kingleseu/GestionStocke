import os
import django
import cloudinary
import cloudinary.uploader
from django.conf import settings
from products.models import Product  # Adaptez selon vos modèles

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

def migrate():
    print("🚀 Début de la migration des images vers Cloudinary...")
    
    # Récupérer tous les produits avec une image
    products = Product.objects.exclude(image='')
    
    for product in products:
        if product.image and not product.image.name.startswith('http'):
            try:
                print(f"📦 Envoi de : {product.image.name}")
                # Le simple fait de sauvegarder à nouveau le modèle avec Cloudinary actif
                # va déclencher l'upload si le stockage est bien configuré.
                product.image.save(product.image.name, product.image.file, save=True)
                print(f"✅ Réussi : {product.image.url}")
            except Exception as e:
                print(f"❌ Erreur sur {product.image.name}: {e}")

    print("🏁 Migration terminée !")

if __name__ == "__main__":
    confirm = input("Voulez-vous vraiment envoyer vos images locales vers Cloudinary ? (y/n) : ")
    if confirm.lower() == 'y':
        migrate()
