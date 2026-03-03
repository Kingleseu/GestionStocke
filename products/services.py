"""
Service de Personnalisation Produit
Moteur de règles basé sur JSON avec validation et pricing sécurisé
"""
import json
import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import ProductCustomizationConfig, CustomizableComponent, CustomizationFont
from typing import Dict, Any, Optional, List


class CustomizationService:
    """
    Moteur de personnalisation complet.
    Gère validation, pricing, et génération de données de production.
    """

    # ==========================================
    # 1. RÉCUPÉRATION DES RÈGLES
    # ==========================================
    
    @staticmethod
    def get_product_rules(product) -> Optional[Dict]:
        """
        Récupère les règles actives.
        Si une config Atelier existe, elle est convertie en structure JSON compatible.
        """
        if not product.is_customizable:
            return None
        
        # 1. Tenter de récupérer la config Atelier structurée
        try:
            config = product.customization_config
            return CustomizationService.convert_studio_config_to_rules(config)
        except:
            pass

        # 2. Surcharge locale (JSON brut legacy)
        if product.customization_rules_override:
            return product.customization_rules_override
        
        # 3. Template global
        if product.customization_template and product.customization_template.is_active:
            return product.customization_template.rules
        
        return None

    @staticmethod
    def convert_studio_config_to_rules(config: ProductCustomizationConfig) -> Dict:
        """
        Convertit un ProductCustomizationConfig en structure de règles JSON exploitable par le moteur.
        """
        rules = {
            "version": "3.0",
            "is_studio": True,
            "zones": [],
            "special_rules": config.studio_config.get('special_rules', {})
        }

        # Ajouter une zone pour le choix du composant (Médaillon)
        components = config.allowed_components.filter(is_active=True)
        if components.exists():
            comp_zone = {
                "id": "studio_component",
                "type": "selection",
                "label": "Choix du modèle",
                "required": True,
                "options": [
                    {
                        "value": str(c.id), 
                        "label": c.name, 
                        "price_modifier": float(c.base_price_modifier),
                        "image_url": c.image.url,
                        "shape": c.shape_identifier
                    } for c in components
                ]
            }
            rules["zones"].append(comp_zone)

        # Ajouter une zone pour la gravure
        fonts = config.allowed_fonts.filter(is_active=True)
        allowed_font_names = [f.font_family for f in fonts]
        
        engraving_zone = {
            "id": "studio_engraving",
            "type": "text",
            "label": "Votre gravure",
            "required": False,
            "constraints": {
                "max_length": config.studio_config.get('max_length', 25),
                "allowed_fonts": allowed_font_names
            },
            "price_formula": config.studio_config.get('price_formula', {"base": float(config.product.engraving_price), "per_char": 0}),
            "preview_config": config.studio_config.get('preview_config', {"position": {"x": 50, "y": 50}, "size": 20})
        }
        rules["zones"].append(engraving_zone)

        return rules

    # ==========================================
    # 2. VALIDATION CONDITIONNELLE
    # ==========================================
    
    @staticmethod
    def _is_zone_active(zone: Dict, user_choices: Dict) -> bool:
        """
        Vérifie si une zone est active selon ses conditions.
        Ex: zone "font" active seulement si choices["type"] == "text"
        """
        conditions = zone.get('conditions', {})
        if not conditions:
            return True
        
        for key, expected_value in conditions.items():
            actual_value = user_choices.get(key)
            
            # Support des valeurs multiples
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    @staticmethod
    def _extract_text_from_value(value: Any) -> str:
        """Extrait le texte d'une valeur (str ou dict)"""
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            return value.get('text', '')
        return ''
    
    @staticmethod
    def _extract_font_from_value(value: Any, default='Arial') -> str:
        """Extrait la police d'une valeur"""
        if isinstance(value, dict):
            return value.get('font', default)
        return default

    # ==========================================
    # 3. VALIDATION COMPLÈTE
    # ==========================================
    
    @staticmethod
    def validate_customization_data(product, customization_data: Dict) -> None:
        """
        Valide les données de personnalisation.
        Lève ValidationError en cas de problème.
        
        Args:
            product: Instance Product
            customization_data: {"choices": {"zone_id": value}}
        
        Raises:
            ValidationError: Si validation échoue
        """
        rules = CustomizationService.get_product_rules(product)
        
        if not rules:
            if customization_data and customization_data.get('choices'):
                raise ValidationError("Ce produit n'est pas personnalisable.")
            return
        
        zones = rules.get('zones', [])
        user_choices = customization_data.get('choices', {})
        
        for zone in zones:
            # Vérifier si la zone est active
            if not CustomizationService._is_zone_active(zone, user_choices):
                continue
            
            zone_id = zone.get('id')
            zone_label = zone.get('label', zone_id)
            is_required = zone.get('required', False)
            zone_type = zone.get('type')
            user_value = user_choices.get(zone_id)
            
            # 1. Vérif Requis
            if is_required and not user_value:
                raise ValidationError(f"Le champ '{zone_label}' est obligatoire.")
            
            if not user_value:
                continue
            
            # 2. Validation selon TYPE
            if zone_type == 'text':
                CustomizationService._validate_text_zone(zone, user_value)
            
            elif zone_type == 'selection':
                CustomizationService._validate_selection_zone(zone, user_value)
            
            elif zone_type == 'image':
                CustomizationService._validate_image_zone(zone, user_value)
    
    @staticmethod
    def _validate_text_zone(zone: Dict, value: Any) -> None:
        """Valide une zone de type texte"""
        text = CustomizationService._extract_text_from_value(value)
        font = CustomizationService._extract_font_from_value(value)
        constraints = zone.get('constraints', {})
        zone_label = zone.get('label', zone['id'])
        
        # Longueur max
        max_length = constraints.get('max_length', 100)
        if len(text) > max_length:
            raise ValidationError(
                f"'{zone_label}': Texte trop long ({len(text)}/{max_length} caractères)."
            )
        
        # Caractères autorisés (regex)
        allowed_chars_pattern = constraints.get('allowed_chars')
        if allowed_chars_pattern:
            if not re.match(allowed_chars_pattern, text):
                raise ValidationError(
                    f"'{zone_label}': Caractères non autorisés dans le texte."
                )
        
        # Police autorisée
        allowed_fonts = constraints.get('allowed_fonts', [])
        if allowed_fonts and font not in allowed_fonts:
            raise ValidationError(
                f"'{zone_label}': Police '{font}' non autorisée."
            )
    
    @staticmethod
    def _validate_selection_zone(zone: Dict, value: str) -> None:
        """Valide une zone de sélection"""
        options = zone.get('options', [])
        valid_values = [opt['value'] for opt in options]
        zone_label = zone.get('label', zone['id'])
        
        if value not in valid_values:
            raise ValidationError(
                f"'{zone_label}': Choix '{value}' invalide."
            )
    
    @staticmethod
    def _validate_image_zone(zone: Dict, value: Any) -> None:
        """Valide une zone image (upload ou URL)"""
        # Pour l'instant simple, on peut ajouter validation taille/format
        if isinstance(value, dict):
            if not value.get('url') and not value.get('file'):
                raise ValidationError("Image requise mais non fournie.")

    # ==========================================
    # 4. CALCUL DE PRIX SÉCURISÉ
    # ==========================================
    
    @staticmethod
    def calculate_customization_price(product, customization_data: Dict) -> Decimal:
        """
        Calcule le coût ADDITIONNEL de personnalisation.
        NE FAIT JAMAIS CONFIANCE AU CLIENT.
        
        Returns:
            Decimal: Coût extra (sans le prix de base du produit)
        """
        rules = CustomizationService.get_product_rules(product)
        if not rules:
            return Decimal('0.00')
        
        extra_cost = Decimal('0.00')
        zones = rules.get('zones', [])
        user_choices = customization_data.get('choices', {})
        
        for zone in zones:
            # Ignorer les zones inactives
            if not CustomizationService._is_zone_active(zone, user_choices):
                continue
            
            zone_id = zone.get('id')
            user_value = user_choices.get(zone_id)
            
            if not user_value:
                continue
            
            price_formula = zone.get('price_formula', {})
            zone_type = zone.get('type')
            
            # TEXTE: base + per_char
            if zone_type == 'text':
                base = Decimal(str(price_formula.get('base', 0)))
                per_char = Decimal(str(price_formula.get('per_char', 0)))
                
                text = CustomizationService._extract_text_from_value(user_value)
                char_count = len(text)
                
                if char_count > 0:
                    extra_cost += base + (char_count * per_char)
            
            # SÉLECTION: price_modifier de l'option
            elif zone_type == 'selection':
                options = zone.get('options', [])
                selected_option = next(
                    (opt for opt in options if opt['value'] == user_value),
                    None
                )
                if selected_option:
                    modifier = Decimal(str(selected_option.get('price_modifier', 0)))
                    extra_cost += modifier
            
            # IMAGE: coût fixe upload
            elif zone_type == 'image':
                upload_cost = Decimal(str(price_formula.get('base', 0)))
                extra_cost += upload_cost
        
        return extra_cost
    
    @staticmethod
    def calculate_total_item_price(product, customization_data: Dict) -> Decimal:
        """
        Prix FINAL unitaire = Prix de base + Options
        à stocker dans price_at_addition
        """
        base_price = product.selling_price
        extra = CustomizationService.calculate_customization_price(product, customization_data)
        return base_price + extra

    # ==========================================
    # 5. GÉNÉRATION DONNÉES PRODUCTION
    # ==========================================
    
    @staticmethod
    def generate_production_data(product, customization_data: Dict) -> Dict:
        """
        Génère les données nettoyées pour l'atelier.
        
        Returns:
            {
                "product_name": "...",
                "barcode": "...",
                "instructions": [
                    {"zone": "Gravure", "action": "Graver 'Marie' en Arial"},
                    {"zone": "Forme", "action": "Ajouter cœur"}
                ],
                "special_notes": "Non remboursable, délai 3j"
            }
        """
        rules = CustomizationService.get_product_rules(product)
        user_choices = customization_data.get('choices', {})
        
        instructions = []
        
        if rules:
            zones = rules.get('zones', [])
            
            for zone in zones:
                if not CustomizationService._is_zone_active(zone, user_choices):
                    continue
                
                zone_id = zone.get('id')
                zone_label = zone.get('label', zone_id)
                user_value = user_choices.get(zone_id)
                
                if not user_value:
                    continue
                
                zone_type = zone.get('type')
                
                if zone_type == 'text':
                    text = CustomizationService._extract_text_from_value(user_value)
                    font = CustomizationService._extract_font_from_value(user_value)
                    instructions.append({
                        "zone": zone_label,
                        "action": f"Graver '{text}' en {font}"
                    })
                
                elif zone_type == 'image':
                    instructions.append({
                        "zone": zone_label,
                        "action": "Graver la photo client"
                    })
                
                elif zone_type == 'selection':
                    options = zone.get('options', [])
                    selected = next((o for o in options if o['value'] == user_value), None)
                    if selected:
                        instructions.append({
                            "zone": zone_label,
                            "action": f"Appliquer: {selected['label']}"
                        })
            
            # Fallback for generic image uploads
        # Fallback for standard keys (Recto/Verso/Studio) if no zone-based instructions were added
        # Ensure we capture images and shapes even in fallback mode
        if not instructions:
            # Side processing (Recto/Verso)
            for side in ['recto', 'verso']:
                side_data = user_choices.get(side)
                if not side_data or not isinstance(side_data, dict):
                    continue
                
                if not side_data.get('active', True):
                    continue

                label = "Recto" if side == "recto" else "Verso"
                
                # Check for images in multiple possible keys
                hasImage = (
                    side_data.get('image_data') or 
                    side_data.get('url') or 
                    side_data.get('file') or 
                    side_data.get('image_preview')
                )
                
                if hasImage:
                    instructions.append({
                        "zone": label,
                        "action": "Graver la photo client"
                    })
                
                if side_data.get('text'):
                    instructions.append({
                        "zone": label,
                        "action": f"Graver '{side_data['text']}' en {side_data.get('font', 'Arial')}"
                    })
            
            # Studio engraving fallback
            studio_engraving_data = user_choices.get('studio_engraving')
            if studio_engraving_data and isinstance(studio_engraving_data, dict):
                label = 'Gravure'
                if studio_engraving_data.get('text'):
                    font = studio_engraving_data.get('font', 'Default')
                    instructions.append({
                        "zone": label,
                        "action": f"Graver '{studio_engraving_data['text']}' en {font}"
                    })
                if studio_engraving_data.get('url') or studio_engraving_data.get('image_data') or studio_engraving_data.get('file'):
                    instructions.append({
                        "zone": label,
                        "action": "Graver la photo client"
                    })
            
            # Forme/Modèle fallback
            model = user_choices.get('studio_component_label') or user_choices.get('studio_component')
            if model:
                # Better label mapping for common IDs
                friendly_labels = {
                    'med': 'Medaillon Millitaire',
                    'heart': 'Cœur',
                    'circle': 'Circulaire',
                    'star': 'Étoile',
                    'africa': 'Afrique',
                }
                model_label = friendly_labels.get(str(model).lower(), model)
                instructions.append({
                    "zone": "Modèle",
                    "action": f"Appliquer: {model_label}"
                })
        
        # Additional cleanup for instruction duplicates or "empty" states
        if not instructions and user_choices:
            # If nothing was added but choices exist, at least add a raw notice
            instructions.append({"zone": "Infos", "action": "Voir détails de personnalisation"})
        
        # Notes spéciales
        special_notes = []
        if not product.is_refundable:
            special_notes.append("❌ PRODUIT NON REMBOURSABLE")
        if product.production_delay_days > 0:
            special_notes.append(f"⏱️ Délai de production: {product.production_delay_days} jours")
        
        return {
            "product_name": product.name,
            "barcode": product.barcode,
            "instructions": instructions,
            "special_notes": "\n".join(special_notes),
            "raw_data": customization_data  # Données brutes en backup
        }

    # ==========================================
    # 6. GÉNÉRATION D'IMAGE (PILLOW)
    # ==========================================
    
    @staticmethod
    def generate_preview_image(product, customization_data: Dict) -> Optional[Any]:
        """
        Génère une image de prévisualisation fusionnée.
        Utilise Pillow pour coller le texte/formes sur le mockup.
        """
        from PIL import Image, ImageDraw, ImageFont
        import io
        from django.core.files.base import ContentFile
        
        if not product.mockup_image:
            return None
            
        try:
            # Ouvrir le mockup
            mockup = Image.open(product.mockup_image.path).convert('RGBA')
            draw = ImageDraw.Draw(mockup)
            
            rules = CustomizationService.get_product_rules(product)
            user_choices = customization_data.get('choices', {})
            
            for zone in rules.get('zones', []):
                if not CustomizationService._is_zone_active(zone, user_choices):
                    continue
                
                zone_id = zone.get('id')
                user_value = user_choices.get(zone_id)
                if not user_value:
                    continue
                
                config = zone.get('preview_config', {})
                pos = config.get('position', {'x': 50, 'y': 50})
                
                # Conversion % en pixels
                pixel_x = (pos['x'] * mockup.width) / 100
                pixel_y = (pos['y'] * mockup.height) / 100
                
                if zone['type'] == 'text':
                    text = CustomizationService._extract_text_from_value(user_value)
                    font_name = CustomizationService._extract_font_from_value(user_value)
                    size = config.get('size', 20)
                    color = config.get('color', '#000000')
                    
                    # Tentative de chargement de police (fallback Arial)
                    try:
                        # On pourrait chercher dans un dossier media/fonts/
                        font = ImageFont.truetype(f"static/fonts/{font_name}.ttf", size)
                    except:
                        font = ImageFont.load_default()
                        
                    draw.text((pixel_x, pixel_y), text, fill=color, font=font, anchor="mm")
                    
                elif (zone['type'] == 'selection' or zone['type'] == 'shape') and user_value:
                    # Render Symbol/Shape
                    # We can use a library of PNG/SVG icons in static/img/symbols/
                    symbol_path = f"static/img/symbols/{user_value}.png"
                    try:
                        symbol_img = Image.open(symbol_path).convert('RGBA')
                        size = config.get('size', 40)
                        symbol_img.thumbnail((size, size))
                        # Center symbol on position
                        mockup.paste(symbol_img, (int(pixel_x - size/2), int(pixel_y - size/2)), symbol_img)
                    except:
                        # Fallback: draw a basic shape or skip
                        pass
            
            # Sauvegarder dans un buffer
            buffer = io.BytesIO()
            mockup.save(buffer, format='PNG')
            return ContentFile(buffer.getvalue(), name=f"preview_{product.id}.png")
            
        except Exception as e:
            print(f"Error generating preview: {e}")
            return None

    # ==========================================
    # 7. UTILITAIRES
    # ==========================================
    
    @staticmethod
    def get_default_template_structure() -> Dict:
        """Structure JSON exemple pour créer un template"""
        return {
            "version": "2.0",
            "zones": [
                {
                    "id": "personalization_type",
                    "type": "selection",
                    "label": "Je personnalise avec...",
                    "required": True,
                    "options": [
                        {"value": "text", "label": "✍️ Un Texte", "price_modifier": 0},
                        {"value": "shape", "label": "✨ Une Forme", "price_modifier": 0}
                    ]
                },
                {
                    "id": "engraving_text",
                    "type": "text",
                    "label": "Votre texte",
                    "required": True,
                    "conditions": {"personalization_type": "text"},
                    "constraints": {
                        "max_length": 25,
                        "allowed_chars": "^[a-zA-Z0-9àéèêëïîôùûçÀÉÈÊËÏÎÔÙÛÇ ,.!?'-]+$",
                        "allowed_fonts": ["Arial", "Playfair Display", "Dancing Script", "Courier New"]
                    },
                    "price_formula": {
                        "base": 5.00,
                        "per_char": 0.00
                    },
                    "preview_config": {
                        "position": {"x": 50, "y": 50},
                        "size": 24,
                        "color": "#1a1a1a"
                    }
                },
                {
                    "id": "shape_choice",
                    "type": "selection",
                    "label": "Choisissez une forme",
                    "required": True,
                    "conditions": {"personalization_type": "shape"},
                    "options": [
                        {"value": "heart", "label": "Cœur ♥", "price_modifier": 3.00},
                        {"value": "star", "label": "Étoile ★", "price_modifier": 3.00},
                        {"value": "infinity", "label": "Infini ∞", "price_modifier": 3.00},
                        {"value": "dogtag", "label": "Plaque (Dog Tag)", "price_modifier": 5.00},
                        {"value": "africa", "label": "Afrique", "price_modifier": 4.00},
                        {"value": "cross", "label": "Croix", "price_modifier": 3.00},
                        {"value": "bar_curved", "label": "Barre Courbée", "price_modifier": 4.00}
                    ],
                    "preview_config": {
                        "position": {"x": 50, "y": 50},
                        "size": 40
                    }
                }
            ],
            "special_rules": {
                "non_refundable": True,
                "production_delay_days": 3,
                "legal_notice": "Les produits personnalisés ne sont ni repris ni échangés."
            }
        }
