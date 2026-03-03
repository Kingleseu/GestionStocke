
from django.core.management.base import BaseCommand
from products.models import CustomizableComponent
import os

class Command(BaseCommand):
    help = 'Populate initial customization shapes'

    def handle(self, *args, **options):
        self.stdout.write("Checking customization shapes...")
        
        shapes = [
            # Original 4
            {"name": "Medallion Heart", "type": "medallion", "id": "heart", "img": "medallion_heart.png"},
            {"name": "Medallion Clover", "type": "medallion", "id": "clover", "img": "medallion_clover.png"},
            {"name": "Medallion Star", "type": "medallion", "id": "star", "img": "medallion_star.png"},
            {"name": "Medallion Round", "type": "medallion", "id": "round", "img": "medallion_round.png"},
            # New 4 (Reverted to Generated/Placeholders)
            {"name": "Medallion Dog Tag", "type": "medallion", "id": "dogtag", "img": "medallion_dogtag.png"},
            {"name": "Medallion Curved Bar", "type": "medallion", "id": "bar_curved", "img": "medallion_bar_curved.png"},
            {"name": "Medallion Africa", "type": "medallion", "id": "africa", "img": "medallion_africa.png"},
            {"name": "Medallion Cross", "type": "medallion", "id": "cross", "img": "medallion_cross.png"},
        ]

        count_created = 0
        count_updated = 0

        for s in shapes:
            db_path = f"customization/components/{s['img']}"
            
            comp, created = CustomizableComponent.objects.get_or_create(
                shape_identifier=s['id'],
                defaults={
                    "name": s['name'],
                    "component_type": s['type'],
                    "image": db_path,
                    "is_active": True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {s['name']}"))
                count_created += 1
            else:
                # Force update to ensure image path and active status are correct
                comp.name = s['name']
                comp.image = db_path
                comp.is_active = True
                comp.save()
                self.stdout.write(f"Updated {s['name']}")
                count_updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done! Created: {count_created}, Updated: {count_updated}"))
        self.stdout.write(f"Total in DB: {CustomizableComponent.objects.count()}")

