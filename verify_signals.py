import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from accounts.models import UserActivity

# Create a test user
user, created = User.objects.get_or_create(username='testbox_verifier')
user.set_password('pass')
user.save()

# Simulate using Client
client = Client()

# Test Login Signal
print("Testing Login Signal...")
client.login(username='testbox_verifier', password='pass')

# Check if activity recorded
activity = UserActivity.objects.filter(user=user, activity_type='LOGIN').first()
if activity:
    print(f"SUCCESS: Login activity found: {activity}")
else:
    print("FAILURE: No login activity found.")

# Test Logout Signal
print("Testing Logout Signal...")
client.logout()

activity = UserActivity.objects.filter(user=user, activity_type='LOGOUT').first()
if activity:
    print(f"SUCCESS: Logout activity found: {activity}")
else:
    print("FAILURE: No logout activity found.")
