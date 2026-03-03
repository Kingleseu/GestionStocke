
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionStocke.settings')
django.setup()

from products.models import CustomizableComponent

components = CustomizableComponent.objects.all()
print(f"Total components: {components.count()}")
for comp in components:
    print(f"ID: {comp.id}, Name: {comp.name}, Image: {comp.image}, Shape: {comp.shape_identifier}")
    if comp.image:
        print(f"  - Image URL: {comp.image.url}")
        print(f"  - Path exists: {os.path.exists(comp.image.path)}")
    else:
        print("  - NO IMAGE")
