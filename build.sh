#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "======================================"
echo "Starting Build Process for Render"
echo "======================================"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

# Verify database connection
echo "🔍 Verifying database connection..."
python manage.py check --database default

# Show migration status
echo "📊 Checking migration status..."
python manage.py showmigrations

# Run migrations with verbose output
echo "🔄 Running database migrations..."
python manage.py migrate --verbosity 2

# Create superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: username=admin, password=admin123')
else:
    print('ℹ️  Superuser already exists')
EOF

echo "======================================"
echo "✅ Build completed successfully!"
echo "======================================"




