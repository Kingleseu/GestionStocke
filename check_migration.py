import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
sys.path.insert(0, os.path.dirname(__file__))

import django
django.setup()

from django.db import models
from supply.models import SupplyCategory
print(f"SupplyCategory exists: {SupplyCategory is not None}")
print(f"Fields: {[f.name for f in SupplyCategory._meta.fields]}")
print(f"Table name: {SupplyCategory._meta.db_table}")