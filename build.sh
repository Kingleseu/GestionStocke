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

# Verify database connection
echo "🔍 Verifying database connection..."
python manage.py check --database default

# Show migration status
echo "📊 Checking migration status..."
python manage.py showmigrations

# Run migrations with verbose output (BEFORE collectstatic)
echo "🔄 Running database migrations..."
python manage.py migrate --verbosity 2

# Collect static files (AFTER migrations)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Verify static files were collected
echo "✅ Verifying static files collection..."
STATIC_FILES_COUNT=$(find staticfiles -type f -not -name '*.gz' 2>/dev/null | wc -l)
echo "📊 Static files collected: $STATIC_FILES_COUNT files"
if [ "$STATIC_FILES_COUNT" -lt 10 ]; then
    echo "⚠️  WARNING: Only $STATIC_FILES_COUNT files collected (expected 50+)"
    find staticfiles -type f -not -name '*.gz' 2>/dev/null | head -20
else
    echo "✅ Static files successfully collected"
fi

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




