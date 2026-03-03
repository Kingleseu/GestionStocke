# -*- coding: utf-8 -*-
"""
Script de setup pour creer des templates et produits de demonstration
Inspire de zagbijoux.fr
"""
import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from products.models import CustomizationTemplate, Product, Category
from products.services import CustomizationService


def create_zag_templates():
    """Creer les templates inspires de zag bijoux"""
    
    print("Creation des templates de personnalisation...")
    
    # Template 1: Gravure Texte Simple (ex: Collier grave)
    template1, created = CustomizationTemplate.objects.get_or_create(
        name="Gravure Texte",
        defaults={
            "description": "Personnalisation par gravure de texte (prenom, date, message)",
            "is_active": True,
            "rules": {
                "version": "2.0",
                "zones": [
                    {
                        "id": "engraving_text",
                        "type": "text",
                        "label": "Votre gravure",
                        "required": True,
                        "constraints": {
                            "max_length": 25,
                            "allowed_chars": "^[a-zA-Z0-9 ,.!?'-]+$",
                            "allowed_fonts": [
                                "Arial",
                                "Playfair Display",
                                "Dancing Script",
                                "Courier New",
                                "Great Vibes"
                            ]
                        },
                        "price_formula": {
                            "base": 5.00,
                            "per_char": 0.00
                        }
                    }
                ],
                "special_rules": {
                    "non_refundable": True,
                    "production_delay_days": 2,
                    "legal_notice": "Produit personnalise : Non repris, non echange"
                }
            }
        }
    )
    status1 = "CREE" if created else "Existant"
    print(f"  {status1}: {template1.name}")
    
    # Template 2: Texte OU Forme (Zag Style)
    template2, created = CustomizationTemplate.objects.get_or_create(
        name="Texte ou Symbole",
        defaults={
            "description": "Choix entre texte personnalise ou symbole grave",
            "is_active": True,
            "rules": {
                "version": "2.0",
                "zones": [
                    {
                        "id": "customization_type",
                        "type": "selection",
                        "label": "Je personnalise avec...",
                        "required": True,
                        "options": [
                            {"value": "text", "label": "Un Texte / Prenom", "price_modifier": 0},
                            {"value": "symbol", "label": "Un Symbole", "price_modifier": 0}
                        ]
                    },
                    {
                        "id": "text_content",
                        "type": "text",
                        "label": "Votre texte",
                        "required": True,
                        "conditions": {"customization_type": "text"},
                        "constraints": {
                            "max_length": 20,
                            "allowed_chars": "^[a-zA-Z0-9 &-]+$",
                            "allowed_fonts": ["Arial", "Dancing Script", "Playfair Display"]
                        },
                        "price_formula": {
                            "base": 5.00,
                            "per_char": 0.00
                        }
                    },
                    {
                        "id": "symbol_choice",
                        "type": "selection",
                        "label": "Choisissez votre symbole",
                        "required": True,
                        "conditions": {"customization_type": "symbol"},
                        "options": [
                            {"value": "heart", "label": "Coeur", "price_modifier": 3.00},
                            {"value": "star", "label": "Etoile", "price_modifier": 3.00},
                            {"value": "infinity", "label": "Infini", "price_modifier": 3.00},
                            {"value": "moon", "label": "Lune", "price_modifier": 3.00},
                            {"value": "sun", "label": "Soleil", "price_modifier": 3.00}
                        ]
                    }
                ],
                "special_rules": {
                    "non_refundable": True,
                    "production_delay_days": 3,
                    "legal_notice": "Article personnalise : Ni repris, ni echange"
                }
            }
        }
    )
    status2 = "CREE" if created else "Existant"
    print(f"  {status2}: {template2.name}")
    
    return template1, template2


def apply_to_products():
    """Appliquer les templates aux produits existants"""
    print("\nApplication aux produits...")
    
    template1, template2 = create_zag_templates()
    
    # Trouver des produits candidats
    colliers = Product.objects.filter(name__icontains="collier")
    
    if colliers.exists():
        count = 0
        for collier in colliers[:3]:  # Prendre 3 colliers
            collier.is_customizable = True
            collier.customization_template = template2  # Texte OU Symbole
            collier.production_delay_days = 3
            collier.is_refundable = False
            collier.save()
            print(f"   OK: {collier.name} -> Personnalisable")
            count += 1
        if count == 0:
            print("   Aucun collier trouve")
    else:
        print("   Aucun collier trouve")
    
    # Autres produits avec gravure simple
    autres = Product.objects.filter(is_customizable=False).exclude(name__icontains="collier")[:2]
    for produit in autres:
        produit.is_customizable = True
        produit.customization_template = template1  # Gravure simple
        produit.production_delay_days = 2
        produit.is_refundable = False
        produit.save()
        print(f"   OK: {produit.name} -> Personnalisable (Gravure)")


def main():
    print("\n" + "="*50)
    print("   SETUP PERSONNALISATION ZAG STYLE")
    print("="*50 + "\n")
    
    create_zag_templates()
    apply_to_products()
    
    # Test structure
    print("\nTest de la structure JSON...")
    default_struct = CustomizationService.get_default_template_structure()
    print(f"   Structure par defaut valide: {len(default_struct['zones'])} zones")
    
    print("\nSetup termine avec succes !")
    print("Allez dans l'admin Django pour voir les templates et produits")
    print("URL: /admin/products/customizationtemplate/\n")


if __name__ == '__main__':
    main()
