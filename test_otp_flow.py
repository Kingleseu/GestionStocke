import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import sys

print("Existing Users:", User.objects.count())

client = Client()
print("1. Submitting manager signup request...")
response = client.post(
    '/accounts/signup/', 
    {
        'shop_name': 'My Shop',
        'first_name': 'Boss',
        'last_name': 'Man',
        'email': 'manager@mkaribu.local',
        'phone': '123456789'
    }
)
print("Status Code:", response.status_code)
if response.status_code == 302:
    print("Redirect to:", response.url)

print("2. Current Session User ID (should be None):", client.session.get('_auth_user_id'))
