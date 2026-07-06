#!/usr/bin/env bash
# Railway startup script
set -e

echo "======================================"
echo "🚂 Railway Deployment Starting"
echo "======================================"

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import sys
from django.core.management import execute_from_command_line
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pembeny.settings')

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        import django
        django.setup()
        from django.db import connection
        connection.ensure_connection()
        print('✅ Database connection successful!')
        break
    except Exception as e:
        retry_count += 1
        print(f'⏳ Waiting for database... ({retry_count}/{max_retries})')
        time.sleep(2)
        if retry_count >= max_retries:
            print('❌ Could not connect to database')
            sys.exit(1)
"

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: username=admin, password=admin123')
    print('⚠️  IMPORTANT: Change this password immediately!')
else:
    print('ℹ️  Superuser already exists')
EOF

echo "======================================"
echo "✅ Deployment setup complete!"
echo "🚀 Starting Gunicorn server..."
echo "======================================"

# Start Gunicorn
exec gunicorn pembeny.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
