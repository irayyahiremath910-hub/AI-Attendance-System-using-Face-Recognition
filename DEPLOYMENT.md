# AI Attendance System - Deployment Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [Static Files & Media](#static-files--media)
6. [Celery & Background Tasks](#celery--background-tasks)
7. [Docker Deployment](#docker-deployment)
8. [Production Deployment](#production-deployment)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

- [ ] All code tested locally
- [ ] Database migrations created and tested
- [ ] Environment variables configured
- [ ] Secret key changed
- [ ] DEBUG set to False
- [ ] ALLOWED_HOSTS configured
- [ ] Security settings enabled
- [ ] Redis/Celery configured
- [ ] Email settings configured
- [ ] SSL certificate obtained
- [ ] Backup strategy defined
- [ ] Monitoring setup completed

---

## Environment Setup

### 1. Clone & Install Dependencies

```bash
git clone <repository-url>
cd AI-Attendance-System-using-Face-Recognition
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Create .env File

```bash
cp .env.example .env
```

Edit `.env` with your production values:

```
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ENVIRONMENT=production

DATABASE_URL=postgresql://user:password@localhost:5432/attendance_db
REDIS_URL=redis://localhost:6379/0

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

FACE_RECOGNITION_THRESHOLD=0.6
MIN_ATTENDANCE_THRESHOLD=75
```

---

## Database Configuration

### PostgreSQL Setup (Recommended)

```bash
# Install PostgreSQL
# Windows: https://www.postgresql.org/download/windows/
# Ubuntu: sudo apt-get install postgresql postgresql-contrib

# Create database and user
psql -U postgres
CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'secure_password';
ALTER ROLE attendance_user SET client_encoding TO 'utf8';
ALTER ROLE attendance_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE attendance_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
\q
```

### Run Migrations

```bash
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
```

---

## Security Configuration

### Generate Secure Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### SSL/HTTPS Setup

For production, use Let's Encrypt with certbot:

```bash
# Install certbot
pip install certbot certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com
```

### Security Headers

The settings.py already includes:
- SECURE_SSL_REDIRECT
- SESSION_COOKIE_SECURE
- CSRF_COOKIE_SECURE
- SECURE_HSTS_SECONDS
- X-Frame-Options protection

### Admin Panel Protection

Change admin URL in `Project101/urls.py`:

```python
path('admin_secret_path_12345/', admin.site.urls),  # Change from /admin/
```

---

## Static Files & Media

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Configure CDN (Optional)

For AWS S3:

```bash
pip install boto3
pip install django-storages
```

Update settings.py:

```python
# AWS S3 Configuration
USE_S3 = config('USE_S3', default=False, cast=bool)

if USE_S3:
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

---

## Celery & Background Tasks

### Install Redis

```bash
# Ubuntu
sudo apt-get install redis-server

# macOS
brew install redis

# Windows: Use WSL or Docker
```

Start Redis:

```bash
redis-server
```

### Start Celery Worker

```bash
celery -A Project101 worker --loglevel=info
```

### Start Celery Beat (Scheduler)

```bash
celery -A Project101 beat --loglevel=info
```

### Monitor Celery

```bash
# Install Flower
pip install flower

# Run Flower
celery -A Project101 flower
# Access at http://localhost:5555
```

---

## Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create static files directory
RUN mkdir -p /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "Project101.wsgi:application"]
```

### Create docker-compose.yml

```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: attendance_db
      POSTGRES_USER: attendance_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://attendance_user:secure_password@db:5432/attendance_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A Project101 worker --loglevel=info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://attendance_user:secure_password@db:5432/attendance_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A Project101 beat --loglevel=info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://attendance_user:secure_password@db:5432/attendance_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Run with Docker

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## Production Deployment

### Using Nginx + Gunicorn

#### Install Nginx & Gunicorn

```bash
pip install gunicorn
sudo apt-get install nginx
```

#### Create Systemd Service Files

**File: `/etc/systemd/system/gunicorn.service`**

```ini
[Unit]
Description=gunicorn daemon for attendance system
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/home/deployment/attendance-system
ExecStart=/home/deployment/attendance-system/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind unix:/run/gunicorn.sock \
    Project101.wsgi:application

[Install]
WantedBy=multi-user.target
```

**File: `/etc/systemd/system/celery.service`**

```ini
[Unit]
Description=Celery worker for attendance system
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/home/deployment/attendance-system
ExecStart=/home/deployment/attendance-system/venv/bin/celery -A Project101 worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid \
    -l info

[Install]
WantedBy=multi-user.target
```

**File: `/etc/systemd/system/celery-beat.service`**

```ini
[Unit]
Description=Celery beat scheduler for attendance system
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/home/deployment/attendance-system
ExecStart=/home/deployment/attendance-system/venv/bin/celery -A Project101 beat \
    --loglevel=info \
    --logfile=/var/log/celery/beat.log \
    --pidfile=/var/run/celery/beat.pid

[Install]
WantedBy=multi-user.target
```

#### Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn celery celery-beat
sudo systemctl start gunicorn celery celery-beat
```

#### Nginx Configuration

**File: `/etc/nginx/sites-available/attendance-system`**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /home/deployment/attendance-system/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /home/deployment/attendance-system/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable Nginx site:

```bash
sudo ln -s /etc/nginx/sites-available/attendance-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Monitoring & Logging

### Setup Logging

Create `/etc/rsyslog.d/30-attendance.conf`:

```
# Attendance System Logs
:programname, isequal, "gunicorn" /var/log/attendance/gunicorn.log
:programname, isequal, "celery" /var/log/attendance/celery.log

& stop
```

### Monitor Application

```bash
# Check service status
sudo systemctl status gunicorn
sudo systemctl status celery
sudo systemctl status celery-beat

# View logs
sudo journalctl -u gunicorn -f
sudo journalctl -u celery -f
sudo tail -f /var/log/nginx/access.log
```

### Setup Monitoring with Prometheus

Install Prometheus and Django metrics exporter:

```bash
pip install django-prometheus
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U attendance_user -d attendance_db

# Check database migrations
python manage.py showmigrations
```

### Celery Tasks Not Running

```bash
# Check Celery worker logs
celery -A Project101 worker --loglevel=debug

# Check Redis connection
redis-cli ping
```

### Static Files Not Loading

```bash
# Recollect static files
python manage.py collectstatic --clear --noinput

# Check permissions
sudo chown -R www-data:www-data /path/to/staticfiles
```

### Email Not Sending

```bash
# Test email configuration
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Performance Issues

- Enable caching with Redis
- Add database indexes: `python manage.py update_attendance_summary`
- Optimize images on upload
- Use CDN for static files
- Monitor with `django-debug-toolbar` in development

---

## Backup Strategy

### Database Backup

```bash
# Create backup
pg_dump -U attendance_user attendance_db > attendance_db_backup.sql

# Restore backup
psql -U attendance_user attendance_db < attendance_db_backup.sql
```

### Media Files Backup

```bash
# Tar media files
tar -czf media_backup.tar.gz media/

# Automated daily backup (cron)
0 2 * * * /backup/backup_attendance.sh
```

---

## Conclusion

Follow this guide for a production-ready deployment. For additional help, refer to Django documentation and component-specific guides.
