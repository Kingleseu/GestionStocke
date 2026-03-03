import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
django.setup()

from django.conf import settings

def check_db_config():
    db = settings.DATABASES['default']
    print(f"DATABASE ENGINE: {db['ENGINE']}")
    if 'sqlite3' in db['ENGINE']:
        print(f"SQLITE FILE: {db['NAME']}")
    else:
        print(f"DB HOST: {db.get('HOST')}")
        print(f"DB NAME: {db.get('NAME')}")

if __name__ == "__main__":
    check_db_config()
