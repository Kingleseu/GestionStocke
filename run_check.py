import sys, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redpos.settings')
sys.path.insert(0, os.path.dirname(__file__))

# Write to absolute path
log_path = os.path.join(os.path.dirname(__file__), 'check_result.txt')

import shutil
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    if '__pycache__' in dirs:
        path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(path)
        except:
            pass
    dirs[:] = [d for d in dirs if d != '__pycache__']

# Also delete all .pyc files
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    for f in files:
        if f.endswith('.pyc'):
            try:
                os.remove(os.path.join(root, f))
            except:
                pass

lines = ["--- Caches cleaned ---"]

import django
from django.conf import settings
from django.core.management import call_command
from io import StringIO

django.setup()
buf = StringIO()
try:
    call_command('check', stdout=buf, stderr=buf)
    lines.append("=== CHECK RESULT ===")
    lines.append(buf.getvalue())
    lines.append("=== CHECK OK ===")
except Exception as e:
    lines.append(f"CHECK ERREUR: {e}")
    import traceback
    lines.append(traceback.format_exc())

# Test aussi migrate
buf2 = StringIO()
try:
    call_command('migrate', 'supply', '0004', '--fake-initial', stdout=buf2, stderr=buf2, skip_checks=True)
    lines.append("=== MIGRATE RESULT ===")
    lines.append(buf2.getvalue())
except Exception as e:
    lines.append(f"MIGRATE ERREUR: {e}")
    import traceback
    lines.append(traceback.format_exc())

with open(log_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Result written to {log_path}")