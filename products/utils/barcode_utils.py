# products/utils/barcode_utils.py

import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
import os
from django.conf import settings


def generate_barcode_image(barcode_number, product_name=None):
    """
    Génère une image de code-barres au format PNG
    
    Args:
        barcode_number (str): Le numéro de code-barres (EAN-13)
        product_name (str): Nom du produit (optionnel, pour l'affichage)
    
    Returns:
        BytesIO: Image du code-barres en mémoire
    """
    # Créer le code-barres EAN-13
    ean = barcode.get('ean13', barcode_number, writer=ImageWriter())
    
    # Options pour l'image
    options = {
        'module_width': 0.3,
        'module_height': 15.0,
        'quiet_zone': 6.5,
        'font_size': 10,
        'text_distance': 5.0,
        'background': 'white',
        'foreground': 'black',
    }
    
    # Générer l'image en mémoire
    buffer = BytesIO()
    ean.write(buffer, options=options)
    buffer.seek(0)
    
    return buffer


def save_barcode_image(barcode_number, product_name, output_path=None):
    """
    Sauvegarde une image de code-barres sur le disque
    
    Args:
        barcode_number (str): Le numéro de code-barres
        product_name (str): Nom du produit
        output_path (str): Chemin de sauvegarde (optionnel)
    
    Returns:
        str: Chemin du fichier sauvegardé
    """
    if output_path is None:
        # Créer le dossier barcodes s'il n'existe pas
        barcode_dir = os.path.join(settings.MEDIA_ROOT, 'barcodes')
        os.makedirs(barcode_dir, exist_ok=True)
        output_path = os.path.join(barcode_dir, f'{barcode_number}.png')
    
    # Générer et sauvegarder l'image
    buffer = generate_barcode_image(barcode_number, product_name)
    
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
    
    return output_path


def validate_ean13(barcode_number):
    """
    Valide un code-barres EAN-13
    
    Args:
        barcode_number (str): Le code-barres à valider
    
    Returns:
        bool: True si valide, False sinon
    """
    if not barcode_number or len(barcode_number) != 13:
        return False
    
    if not barcode_number.isdigit():
        return False
    
    # Vérifier le checksum
    code = barcode_number[:12]
    checksum = int(barcode_number[12])
    
    odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code[i]) for i in range(1, 12, 2))
    total = odd_sum + (even_sum * 3)
    calculated_checksum = (10 - (total % 10)) % 10
    
    return checksum == calculated_checksum
