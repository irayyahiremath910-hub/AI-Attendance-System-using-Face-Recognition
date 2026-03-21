@echo off
REM AI Attendance System Setup Script for Windows

echo ==========================================
echo AI Attendance System - Setup Script
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)
python --version
echo ✓ Python found
echo.

REM Create virtual environment if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
echo ✓ Pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo ✓ Dependencies installed
echo.

REM Create .env file if not exists
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo ✓ .env file created - IMPORTANT: Update with your configuration!
) else (
    echo ✓ .env file already exists
)
echo.

REM Run migrations
echo Running database migrations...
python manage.py migrate
echo ✓ Migrations completed
echo.

REM Create superuser
echo Creating superuser...
python manage.py createsuperuser
echo ✓ Superuser created
echo.

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput
echo ✓ Static files collected
echo.

REM Create necessary directories
echo Creating necessary directories...
if not exist "media" mkdir media
if not exist "logs" mkdir logs
if not exist "staticfiles" mkdir staticfiles
echo ✓ Directories created
echo.

echo ==========================================
echo Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Update .env file with your configuration
echo 2. Start Redis: redis-server
echo 3. Start Celery worker: celery -A Project101 worker --loglevel=info
echo 4. Start Celery beat: celery -A Project101 beat --loglevel=info
echo 5. Run server: python manage.py runserver
echo.
echo Access the application at http://localhost:8000
echo Admin panel at http://localhost:8000/admin
echo.
pause
