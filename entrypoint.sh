#!/bin/bash
# Startup script for the application container

set -e

echo "Starting AI Attendance System..."
echo ""

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z -w 2 $DB_HOST $DB_PORT 2>/dev/null; do
    echo "  PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "✓ PostgreSQL is ready"
echo ""

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput
echo "✓ Migrations completed"
echo ""

# Create superuser if it doesn't exist (optional)
# Uncomment to enable
# echo "Creating superuser..."
# python manage.py shell << END
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'admin')
#     print("Superuser created")
# else:
#     print("Superuser already exists")
# END

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "✓ Static files collected"
echo ""

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    Project101.wsgi:application
