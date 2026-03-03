import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizableComponent
from django.conf import settings

print("="*50)
print("DEBUG: Component Images")
print("="*50)

print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"MEDIA_URL: {settings.MEDIA_URL}")
print("-" * 50)

components = CustomizableComponent.objects.all()
for comp in components:
    print(f"Component: {comp.name}")
    print(f"  ID: {comp.id}")
    print(f"  Image Field Value (raw): '{comp.image}'")
    
    if comp.image:
        try:
            print(f"  Image Name: {comp.image.name}")
            print(f"  Image URL: {comp.image.url}")
            print(f"  Image Path: {comp.image.path}")
            print(f"  File Exists: {os.path.exists(comp.image.path)}")
        except Exception as e:
            print(f"  ERROR accessing image prop: {e}")
    else:
        print("  Image Field is logically empty/None")
    
    print("-" * 30)
