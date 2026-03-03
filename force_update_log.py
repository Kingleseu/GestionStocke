
import os
import django
import sys

# Redirect stdout/stderr to a file
sys.stdout = open('debug_log.txt', 'w')
sys.stderr = sys.stdout

print("Starting update script...")

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
    print("Settings configured.")
    
    django.setup()
    print("Django setup complete.")

    from products.models import CustomizableComponent

    print("Fetching components...")
    components = CustomizableComponent.objects.all()
    print(f"Found {components.count()} components.")

    updates = [
        ("Heart", "customization/components/medallion_heart.png"),
        ("Clover", "customization/components/medallion_clover.png"),
        ("Star", "customization/components/medallion_star.png"),
        ("Round", "customization/components/medallion_round.png"),
    ]

    for name_part, image_path in updates:
        print(f"Processing {name_part}...")
        comp = components.filter(name__icontains=name_part).first()
        if comp:
            print(f"  Found {comp.name}. Updating image to '{image_path}'")
            comp.image = image_path
            comp.save()
            print("  Saved.")
        else:
            print("  Not found.")

    print("\nFinal State:")
    for comp in CustomizableComponent.objects.all():
        print(f"  {comp.name}: '{comp.image}'")

    print("Done.")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()

sys.stdout.close()
