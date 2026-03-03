"""
Script de setup pour créer des templates et produits de démonstration
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
    """Créer les templates inspirés de zag bijoux"""
    
    print("🔧 Création des templates de personnalisation...")
    
    # Template 1: Gravure Texte Simple (ex: Collier gravé)
    template1, created = CustomizationTemplate.objects.get_or_create(
        name="Gravure Texte",
        defaults={
            "description": "Personnalisation par gravure de texte (prénom, date, message)",
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
                            "allowed_chars": "^[a-zA-ZÀ-ÿ0-9 ,.!?'❤♥-]+$",
                            "allowed_fonts": [
                                "Arial",
                                "Playfair Display",
                                "Dancing Script",
                                "Great Vibes",
                                "Cinzel",
                                "Montserrat",
                                "Myriad Pro Regular",
                                "Myriad Pro Bold",
                                "Myriad Pro Semibold"
                            ]
                        },
                        "price_formula": {
                            "base": 5.00,
                            "per_char": 0.00
                        },
                        "preview_config": {
                            "position": {"x": 50, "y": 50},
                            "size": 14,
                            "color": "#000000"
                        }
                    }
                ],
                "special_rules": {
                    "non_refundable": True,
                    "production_delay_days": 2,
                    "legal_notice": "⚠️ Produit personnalisé : Non repris, non échangé"
                }
            }
        }
    )
    print(f"{'✅ Créé' if created else '✓ Existant'}: {template1.name}")
    
    # Template 2: Texte OU Forme (Zag Style)
    template2, created = CustomizationTemplate.objects.get_or_create(
        name="Texte ou Symbole",
        defaults={
            "description": "Choix entre texte personnalisé ou symbole gravé",
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
                            {"value": "text", "label": "✍️ Un Texte / Prénom", "price_modifier": 0},
                            {"value": "symbol", "label": "✨ Un Symbole", "price_modifier": 0}
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
                            "allowed_chars": "^[a-zA-ZÀ-ÿ0-9 ❤♥&-]+$",
                            "allowed_fonts": [
                                "Arial", 
                                "Dancing Script", 
                                "Playfair Display",
                                "Great Vibes",
                                "Cinzel",
                                "Myriad Pro Regular",
                                "Myriad Pro Semibold"
                            ]
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
                            {"value": "heart", "label": "♥ Cœur", "price_modifier": 3.00},
                            {"value": "star", "label": "★ Étoile", "price_modifier": 3.00},
                            {"value": "infinity", "label": "∞ Infini", "price_modifier": 3.00},
                            {"value": "moon", "label": "☽ Lune", "price_modifier": 3.00},
                            {"value": "sun", "label": "☀ Soleil", "price_modifier": 3.00}
                        ]
                    }
                ],
                "special_rules": {
                    "non_refundable": True,
                    "production_delay_days": 3,
                    "legal_notice": "⚠️ Article personnalisé : Ni repris, ni échangé"
                }
            }
        }
    )
    print(f"{'✅ Créé' if created else '✓ Existant'}: {template2.name}")
    
    # Template 3: Personnalisation Complète (Texte + Photo + Forme)
    template3, created = CustomizationTemplate.objects.get_or_create(
        name="Personnalisation Complète",
        defaults={
            "description": "Texte, Photo, et/ou Symbole",
            "is_active": True,
            "rules": {
                "version": "2.0",
                "zones": [
                    {
                        "id": "has_text",
                        "type": "selection",
                        "label": "Ajouter un texte ?",
                        "required": False,
                        "options": [
                            {"value": "yes", "label": "Oui", "price_modifier": 0},
                            {"value": "no", "label": "Non", "price_modifier": 0}
                        ]
                    },
                    {
                        "id": "text_zone",
                        "type": "text",
                        "label": "Votre message",
                        "required": False,
                        "conditions": {"has_text": "yes"},
                        "constraints": {
                            "max_length": 30,
                            "allowed_fonts": [
                                "Arial", 
                                "Dancing Script", 
                                "Playfair Display",
                                "Montserrat",
                                "Myriad Pro Regular"
                            ]
                        },
                        "price_formula": {
                            "base": 8.00,
                            "per_char": 0.20
                        }
                    },
                    {
                        "id": "has_photo",
                        "type": "selection",
                        "label": "Ajouter une photo ?",
                        "required": False,
                        "options": [
                            {"value": "yes", "label": "Oui", "price_modifier": 10.00},
                            {"value": "no", "label": "Non", "price_modifier": 0}
                        ]
                    },
                    {
                        "id": "photo_upload",
                        "type": "image",
                        "label": "Votre photo",
                        "required": False,
                        "conditions": {"has_photo": "yes"},
                        "price_formula": {
                            "base": 0.00
                        }
                    }
                ],
                "special_rules": {
                    "non_refundable": True,
                    "production_delay_days": 5,
                    "legal_notice": "⚠️ Produit unique personnalisé : Aucun retour possible"
                }
            }
        }
    )
    print(f"{'✅ Créé' if created else '✓ Existant'}: {template3.name}")
    
    return template1, template2, template3


def apply_to_products():
    """Appliquer les templates aux produits existants"""
    print("\n📦 Application aux produits...")
    
    template1, template2, template3 = create_zag_templates()
    
    # Trouver des produits candidats
    colliers = Product.objects.filter(name__icontains="collier")
    
    if colliers.exists():
        for collier in colliers[:3]:  # Prendre 3 colliers
            collier.is_customizable = True
            collier.customization_template = template2  # Texte OU Symbole
            collier.production_delay_days = 3
            collier.is_refundable = False
            collier.save()
            print(f"   ✓ {collier.name} → Personnalisable (Texte ou Symbole)")
    
    # Autres produits avec gravure simple
    autres = Product.objects.filter(is_customizable=False).exclude(name__icontains="collier")[:2]
    for produit in autres:
        produit.is_customizable = True
        produit.customization_template = template1  # Gravure simple
        produit.production_delay_days = 2
        produit.is_refundable = False
        produit.save()
        print(f"   ✓ {produit.name} → Personnalisable (Gravure)")


def main():
    print("\n╔═══════════════════════════════════════════╗")
    print("║   🚀 SETUP PERSONNALISATION ZAG STYLE   ║")
    print("╚═══════════════════════════════════════════╝\n")
    
    create_zag_templates()
    apply_to_products()
    
    # Test structure
    print("\n🧪 Test de la structure JSON...")
    default_struct = CustomizationService.get_default_template_structure()
    print(f"   ✓ Structure par défaut valide: {len(default_struct['zones'])} zones")
    
    print("\n✅ Setup terminé avec succès !")
    print("👉 Allez dans l'admin Django pour voir les templates et produits")
    print("👉 URL: /admin/products/customizationtemplate/")


if __name__ == '__main__':
    main()
