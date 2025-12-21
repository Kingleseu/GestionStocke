import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile, Shop

def fix_accounts():
    print("Fixing accounts...")
    users = User.objects.all()
    for user in users:
        # Trigger post_save signal logic manually or save user to trigger it
        # But signals might not be connected if not fully loaded, so let's be explicit
        
        # 1. Create Profile if missing
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            print(f"Created profile for {user.username}")
        
        # 2. If Superuser, ensure Shop
        if user.is_superuser and not profile.shop:
            shop, created = Shop.objects.get_or_create(
                name="Boutique Admin",
                defaults={'created_by': user}
            )
            profile.shop = shop
            profile.save()
            print(f"Assigned '{shop.name}' to admin {user.username}")
            
    print("Done.")

if __name__ == '__main__':
    fix_accounts()
