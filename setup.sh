#!/bin/bash

# AI Attendance System Setup Script
# This script sets up the project for development

echo "=========================================="
echo "AI Attendance System - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 found"
echo ""

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "✓ Pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created - IMPORTANT: Update with your configuration!"
else
    echo "✓ .env file already exists"
fi
echo ""

# Run migrations
echo "Running database migrations..."
python manage.py migrate
echo "✓ Migrations completed"
echo ""

# Create superuser
echo "Creating superuser..."
python manage.py createsuperuser
echo "✓ Superuser created"
echo ""

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "✓ Static files collected"
echo ""

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p media logs staticfiles
echo "✓ Directories created"
echo ""

echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Start Redis: redis-server"
echo "3. Start Celery worker: celery -A Project101 worker --loglevel=info"
echo "4. Start Celery beat: celery -A Project101 beat --loglevel=info"
echo "5. Run server: python manage.py runserver"
echo ""
echo "Access the application at http://localhost:8000"
echo "Admin panel at http://localhost:8000/admin"
echo ""
