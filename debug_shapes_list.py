
import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizableComponent

output_file = "shapes_debug_dump.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"Database: {django.conf.settings.DATABASES['default']['NAME']}\n")
    f.write("="*40 + "\n")
    
    comps = CustomizableComponent.objects.all()
    f.write(f"Total Components: {comps.count()}\n\n")
    
    for c in comps:
        f.write(f"ID: {c.id}\n")
        f.write(f"Name: {c.name}\n")
        f.write(f"Identifier: {c.shape_identifier}\n")
        f.write(f"Active: {c.is_active}\n")
        f.write(f"Image: {c.image}\n")
        f.write("-" * 20 + "\n")
        
print(f"Dumped to {output_file}")
