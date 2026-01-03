import os
import django
from django.urls import get_resolver, reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

resolver = get_resolver()

print("--- URL Check ---")
try:
    url = reverse('store:admin_shop_update')
    print(f"Success: {url}")
except Exception as e:
    print(f"Failed: {e}")

print("\n--- 'store' Namespace reverse_dict keys ---")
# Filter keys that look like 'store:...'
store_keys = [k for k in resolver.reverse_dict.keys() if isinstance(k, str) and k.startswith('store:')]
# Also check NamespacedKey (Django 2.0+)
namespaces = resolver.namespace_dict
print(f"Namespaces: {list(namespaces.keys())}")

if 'store' in namespaces:
    store_urls = namespaces['store'][1]
    print(f"Names in 'store' namespace: {list(store_urls.reverse_dict.keys())}")
