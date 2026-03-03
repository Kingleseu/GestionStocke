#!/usr/bin/env python
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from django.test import Client
from products.models import Product

# Create a test client
client = Client()

# Get the first customizable product
product = Product.objects.filter(is_customizable=True).first()
if product:
    print(f"Testing product: {product.id} - {product.name}")
    
    # Test the public endpoint
    url = f'/store/api/product/{product.id}/customization-data/'
    print(f"Calling: {url}")
    
    response = client.get(url)
    print(f"Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"Content: {response.content.decode()[:1000]}")
else:
    print("No customizable products found")

