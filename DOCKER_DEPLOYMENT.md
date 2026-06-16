# Docker Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the AI Attendance System using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)
- Git
- At least 2GB of free disk space
- Ports 80, 443, 5432, and 8000 available

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/AI-Attendance-System-using-Face-Recognition.git
cd AI-Attendance-System-using-Face-Recognition
```

### 2. Configure Environment
```bash
# Copy the production environment template
cp .env.production.template .env.production

# Edit with your settings
nano .env.production
```

**Important Settings to Configure:**
- `SECRET_KEY`: Generate a secure key with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS`: Your domain names
- `DB_PASSWORD`: Strong database password
- Security settings (SSL, HSTS, etc.)

### 3. Deploy Application
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

This script will:
- Build Docker images
- Start all services
- Run database migrations
- Collect static files
- Verify deployment

### 4. Verify Deployment
```bash
# Check service status
docker-compose ps

# View application logs
docker-compose logs -f web

# Run health checks
chmod +x health_check.sh
./health_check.sh
```

## Service Architecture

### Web Service (Django Application)
- **Container**: ai_attendance_web
- **Port**: 8000 (internal), exposed to Nginx
- **Technology**: Gunicorn + Django
- **Health Check**: Every 30 seconds

### Database Service (PostgreSQL)
- **Container**: ai_attendance_db
- **Port**: 5432
- **Technology**: PostgreSQL 16
- **Volume**: db_data (persistent storage)
- **Health Check**: Every 10 seconds

### Reverse Proxy (Nginx)
- **Container**: ai_attendance_nginx
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Features**: SSL termination, compression, caching
- **Configuration**: nginx.conf

## Common Operations

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100
```

### Run Django Commands
```bash
# Database migration
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Django shell
docker-compose exec web python manage.py shell

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Database Operations
```bash
# Backup database
./backup.sh

# Access database shell
docker-compose exec db psql -U postgres -d attendance_db

# Restore from backup
docker-compose exec -T db psql -U postgres -d attendance_db < backups/attendance_db_20240101_120000.sql
```

### Stop Services
```bash
# Stop services (keeps data)
docker-compose down

# Remove everything (deletes data and images)
docker-compose down -v

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart web
```

## Production Deployment Checklist

- [ ] Configure `.env.production` with all required values
- [ ] Ensure SECRET_KEY is unique and strong
- [ ] Set ALLOWED_HOSTS to your domain(s)
- [ ] Enable SSL/HTTPS (configure reverse proxy)
- [ ] Configure email settings
- [ ] Set up database backups
- [ ] Configure log aggregation (optional)
- [ ] Set up monitoring and alerts (optional)
- [ ] Test all critical user flows
- [ ] Run health checks
- [ ] Set up auto-restart policies

## Scaling and Performance

### Increase Web Workers
Edit `docker-compose.yml` and update the Gunicorn command:
```yaml
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "8", ...]
```

### Enable Redis Caching
1. Add Redis service to `docker-compose.yml`
2. Update Django settings to use Redis cache
3. Restart services

### Database Connection Pooling
Configure in `docker-compose.yml`:
```yaml
environment:
  - CONN_MAX_AGE=600
```

## Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs web

# Verify database connection
docker-compose exec web python manage.py dbshell

# Run diagnostics
docker-compose exec web python manage.py check --deploy
```

### Port already in use
```bash
# Find process using port
lsof -i :8000

# Change port in docker-compose.yml
# Or kill the process
kill -9 <PID>
```

### Database connection error
```bash
# Check database status
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Static files not loading
```bash
# Collect static files again
docker-compose exec web python manage.py collectstatic --noinput

# Check file permissions
docker-compose exec web ls -la /app/static/
```

## Security Considerations

### SSL/HTTPS
For production, configure SSL in Nginx:
1. Obtain SSL certificate (Let's Encrypt recommended)
2. Update `nginx.conf` with certificate paths
3. Enable `SECURE_SSL_REDIRECT` in settings

### Database Access
- Change default PostgreSQL password
- Use strong passwords for database users
- Restrict database access to internal network
- Enable SSL connections between app and database

### Backups
- Set up automated daily backups
- Store backups in secure location
- Test backup restoration regularly
- Keep backup retention policy

### Updates
- Regularly update Docker images
- Update Python dependencies
- Monitor security advisories
- Test updates in staging environment

## Monitoring

### View Resource Usage
```bash
docker stats

# Watch in real-time
docker stats --no-stream=false
```

### Set Up Health Monitoring
```bash
# Add monitoring tools to docker-compose.yml
# Examples: Prometheus, Grafana, ELK Stack
```

## Support and Documentation

- Django Documentation: https://docs.djangoproject.com/
- Docker Documentation: https://docs.docker.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Gunicorn Documentation: https://gunicorn.org/

## Version History

- v1.0.0 (2024): Initial Docker deployment setup
