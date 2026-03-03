
import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizationTemplate, Product

def setup_zag_customization():
    print("Setting up Zag-style customization...")
    
    rules = {
      "version": "2.0",
      "zones": [
        {
          "id": "type",
          "type": "selection",
          "label": "Je personnalise avec...",
          "required": True,
          "options": [
            {"value": "text", "label": "Un Texte / Prénom", "price_modifier": 0},
            {"value": "shape", "label": "Une Forme Géométrique", "price_modifier": 0}
          ]
        },
        {
          "id": "text_content",
          "type": "text",
          "label": "Votre message",
          "required": True,
          "conditions": {"type": "text"},
          "constraints": {
            "max_length": 20,
            "allowed_fonts": ["Arial", "Playfair Display", "Dancing Script", "Courier New", "Great Vibes"]
          },
          "price_formula": {
            "base": 5.00,
            "per_char": 0.00
          }
        },
        {
          "id": "shape_choice",
          "type": "selection",
          "label": "Choisissez une forme",
          "required": True,
          "conditions": {"type": "shape"},
          "options": [
            {"value": "heart", "label": "Cœur", "price_modifier": 3.00},
            {"value": "star", "label": "Étoile", "price_modifier": 3.00},
            {"value": "infinity", "label": "Infini", "price_modifier": 3.00},
            {"value": "clover", "label": "Trèfle", "price_modifier": 3.00}
          ],
          "price_formula": {"base": 0.00}
        }
      ]
    }

    template, created = CustomizationTemplate.objects.get_or_create(
        name="Zag Customization (Text or Shape)",
        defaults={
            "description": "Règles Zag Bijoux: Choix entre Texte ou Forme",
            "rules": rules
        }
    )
    
    if not created:
        template.rules = rules
        template.save()
        print(f"Updated existing template: {template.name}")
    else:
        print(f"Created new template: {template.name}")
        
    # Find a product to attach to (or creating one)
    # Trying to find "Collier" or similar
    product = Product.objects.filter(name__icontains="Collier").first()
    if not product:
        product = Product.objects.first()
        
    if product:
        product.is_customizable = True
        product.customization_template = template
        product.customization_rules = {} # Clear overrides
        product.save()
        print(f"Attached template to product: {product.name} (ID: {product.id})")
    else:
        print("No product found to attach template.")

if __name__ == '__main__':
    setup_zag_customization()
