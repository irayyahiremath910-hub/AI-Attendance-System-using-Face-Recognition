# Environment Variables Reference

Complete reference for all environment variables used in the AI Attendance System.

## Core Django Settings

### `SECRET_KEY`
- **Type**: String
- **Default**: None (Required)
- **Description**: Secret key for Django's cryptographic signing
- **Usage**: `SECRET_KEY=your-random-secret-key-here`
- **Generation**: `python manage.py shell -> from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())`
- **Security**: NEVER commit this to version control. Generate unique value for each environment.
- **Min Length**: 50 characters recommended

### `DEBUG`
- **Type**: Boolean (True/False)
- **Default**: False
- **Description**: Debug mode - MUST be False in production
- **Usage**: `DEBUG=False`
- **Warning**: Never set to True in production!
- **Development**: Can be True for local development

### `ALLOWED_HOSTS`
- **Type**: Comma-separated string
- **Default**: localhost,127.0.0.1
- **Description**: Allowed hostnames for the application
- **Usage**: `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com`
- **Note**: Use IP addresses carefully; domain names are preferred

## Database Configuration

### SQLite (Development)
```env
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### PostgreSQL (Production - Recommended)
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=ai_attendance_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
DB_CONN_MAX_AGE=600
DATABASE_CONNECTION_POOL_SIZE=10
DATABASE_POOL_TIMEOUT=30
```

### Individual Database Variables

#### `DB_ENGINE`
- **Type**: String
- **Options**: `django.db.backends.sqlite3`, `django.db.backends.postgresql`, `django.db.backends.mysql`
- **Default**: `django.db.backends.sqlite3`
- **Description**: Database backend to use
- **Production**: Use PostgreSQL

#### `DB_NAME`
- **Type**: String
- **SQLite**: Path to database file (e.g., `db.sqlite3`)
- **PostgreSQL**: Database name (e.g., `ai_attendance_db`)
- **Default**: `db.sqlite3`

#### `DB_USER`
- **Type**: String
- **Default**: `postgres` (PostgreSQL default)
- **Description**: Database user
- **Security**: Use separate user with minimal privileges

#### `DB_PASSWORD`
- **Type**: String
- **Default**: Empty
- **Description**: Database password
- **Security**: Use strong, randomly generated password

#### `DB_HOST`
- **Type**: String
- **Default**: `localhost`
- **Description**: Database host address
- **Examples**: `localhost`, `db.example.com`, `192.168.1.100`

#### `DB_PORT`
- **Type**: Integer
- **Default**: `5432` (PostgreSQL default)
- **Description**: Database port
- **PostgreSQL**: 5432
- **MySQL**: 3306

#### `DB_CONN_MAX_AGE`
- **Type**: Integer (seconds)
- **Default**: `600`
- **Description**: Database connection age limit
- **Note**: Set to 0 to disable connection pooling

#### `DATABASE_CONNECTION_POOL_SIZE`
- **Type**: Integer
- **Default**: `10`
- **Description**: Number of connections in pool

#### `DATABASE_POOL_TIMEOUT`
- **Type**: Integer (seconds)
- **Default**: `30`
- **Description**: Connection pool timeout

## Security Settings

### `SECURE_SSL_REDIRECT`
- **Type**: Boolean
- **Default**: False
- **Production**: True
- **Description**: Redirect HTTP to HTTPS

### `SESSION_COOKIE_SECURE`
- **Type**: Boolean
- **Default**: False
- **Production**: True
- **Description**: Send session cookies only over HTTPS

### `CSRF_COOKIE_SECURE`
- **Type**: Boolean
- **Default**: False
- **Production**: True
- **Description**: Send CSRF cookies only over HTTPS

### `SESSION_COOKIE_HTTPONLY`
- **Type**: Boolean
- **Default**: True
- **Description**: Session cookies inaccessible to JavaScript

### `CSRF_COOKIE_HTTPONLY`
- **Type**: Boolean
- **Default**: True
- **Description**: CSRF tokens inaccessible to JavaScript

### `CSRF_COOKIE_SAMESITE`
- **Type**: String
- **Options**: `Strict`, `Lax`, `None`
- **Default**: `Strict`
- **Description**: CSRF cookie SameSite attribute

### `SESSION_COOKIE_SAMESITE`
- **Type**: String
- **Options**: `Strict`, `Lax`, `None`
- **Default**: `Strict`
- **Description**: Session cookie SameSite attribute

### `SESSION_COOKIE_AGE`
- **Type**: Integer (seconds)
- **Default**: `86400` (24 hours)
- **Description**: Session timeout duration

### `SECURE_HSTS_SECONDS`
- **Type**: Integer (seconds)
- **Default**: `31536000` (1 year)
- **Description**: HSTS max-age value

### `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- **Type**: Boolean
- **Default**: True
- **Description**: Apply HSTS to subdomains

### `SECURE_HSTS_PRELOAD`
- **Type**: Boolean
- **Default**: True
- **Description**: Enable HSTS preload

### `SECURE_BROWSER_XSS_FILTER`
- **Type**: Boolean
- **Default**: True
- **Description**: Enable XSS filter in browsers

### `X_FRAME_OPTIONS`
- **Type**: String
- **Options**: `DENY`, `SAMEORIGIN`, `ALLOW-FROM`
- **Default**: `DENY`
- **Description**: Clickjacking protection

### `SECURE_CONTENT_SECURITY_POLICY`
- **Type**: String (CSP header value)
- **Default**: `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';`
- **Description**: Content Security Policy header

## Application Settings

### `TIME_ZONE`
- **Type**: String (IANA timezone)
- **Default**: `Asia/Riyadh`
- **Examples**: `UTC`, `America/New_York`, `Europe/London`, `Asia/Tokyo`

### `LANGUAGE_CODE`
- **Type**: String (language code)
- **Default**: `en-us`
- **Examples**: `en-us`, `es-es`, `fr-fr`, `ar-sa`

### `USE_I18N`
- **Type**: Boolean
- **Default**: True
- **Description**: Enable internationalization

### `USE_TZ`
- **Type**: Boolean
- **Default**: True
- **Description**: Use timezone-aware datetimes

### `STATIC_URL`
- **Type**: String (URL path)
- **Default**: `/static/`
- **Description**: URL prefix for static files

### `STATIC_ROOT`
- **Type**: String (file path)
- **Default**: `staticfiles/`
- **Description**: Directory where static files are collected

### `MEDIA_URL`
- **Type**: String (URL path)
- **Default**: `/media/`
- **Description**: URL prefix for user-uploaded files

### `MEDIA_ROOT`
- **Type**: String (file path)
- **Default**: `media/`
- **Description**: Directory for user-uploaded files

## Email Configuration

### `EMAIL_BACKEND`
- **Type**: String (Python module path)
- **Default**: `django.core.mail.backends.smtp.EmailBackend`
- **Options**: `smtp.EmailBackend`, `console.EmailBackend`, `locmem.EmailBackend`

### `EMAIL_HOST`
- **Type**: String (hostname)
- **Default**: `smtp.gmail.com` (example)
- **Examples**: `smtp.gmail.com`, `smtp.sendgrid.net`, `your-smtp.example.com`

### `EMAIL_PORT`
- **Type**: Integer
- **Default**: `587` (TLS)
- **Options**: `587` (TLS), `465` (SSL), `25` (unencrypted)

### `EMAIL_USE_TLS`
- **Type**: Boolean
- **Default**: True
- **Description**: Use TLS encryption

### `EMAIL_HOST_USER`
- **Type**: String (email address)
- **Description**: SMTP authentication username

### `EMAIL_HOST_PASSWORD`
- **Type**: String
- **Description**: SMTP authentication password
- **Security**: Use app-specific password for Gmail

### `DEFAULT_FROM_EMAIL`
- **Type**: String (email address)
- **Default**: `webmaster@localhost`
- **Description**: Default sender email address

## AWS S3 Configuration

### `USE_S3`
- **Type**: Boolean
- **Default**: False
- **Description**: Enable AWS S3 for file storage

### `AWS_ACCESS_KEY_ID`
- **Type**: String
- **Description**: AWS access key
- **Security**: Use IAM user with S3 permissions only

### `AWS_SECRET_ACCESS_KEY`
- **Type**: String
- **Description**: AWS secret access key
- **Security**: NEVER commit to version control

### `AWS_STORAGE_BUCKET_NAME`
- **Type**: String
- **Description**: S3 bucket name (must be globally unique)
- **Example**: `ai-attendance-system-production`

### `AWS_S3_REGION_NAME`
- **Type**: String
- **Default**: `us-east-1`
- **Description**: AWS region for S3 bucket

### `AWS_S3_CUSTOM_DOMAIN`
- **Type**: String
- **Description**: Custom domain for S3 URLs (optional)

## Redis/Cache Configuration

### `REDIS_HOST`
- **Type**: String
- **Default**: `localhost`
- **Description**: Redis server hostname

### `REDIS_PORT`
- **Type**: Integer
- **Default**: `6379`
- **Description**: Redis server port

### `REDIS_PASSWORD`
- **Type**: String
- **Default**: Empty
- **Description**: Redis authentication password

### `REDIS_DB`
- **Type**: Integer
- **Default**: `0`
- **Description**: Redis database number (0-15)

## API Rate Limiting

### `RATELIMIT_ENABLE`
- **Type**: Boolean
- **Default**: True
- **Description**: Enable API rate limiting

### `RATELIMIT_USE_CACHE`
- **Type**: String
- **Default**: `cache`
- **Description**: Cache backend for rate limiting

## Face Recognition

### `FACE_RECOGNITION_MODEL`
- **Type**: String
- **Options**: `hog`, `cnn`, `dlib`
- **Default**: `hog`
- **Description**: Face detection model
- **Performance**: hog < cnn < dlib (faster to slower/better)

### `MIN_FACE_CONFIDENCE`
- **Type**: Float (0.0-1.0)
- **Default**: `0.6`
- **Description**: Minimum confidence for face recognition (60%)
- **Range**: 0.0 (very lenient) to 1.0 (very strict)

## Logging

### `LOG_LEVEL`
- **Type**: String
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Default**: `INFO`
- **Production**: INFO or WARNING

### `SENTRY_DSN`
- **Type**: String (Sentry URL)
- **Description**: Sentry error tracking DSN
- **Optional**: Only if using Sentry

## Celery Configuration (if using async tasks)

### `CELERY_BROKER_URL`
- **Type**: String (Broker URL)
- **Default**: `redis://localhost:6379/0`
- **Description**: Message broker for Celery

### `CELERY_RESULT_BACKEND`
- **Type**: String (Backend URL)
- **Default**: `redis://localhost:6379/0`
- **Description**: Result backend for Celery

## Admin Configuration

### `DJANGO_ADMIN_URL`
- **Type**: String (URL path)
- **Default**: `admin/`
- **Description**: URL path for Django admin
- **Security**: Change from default to obscure in production

## Example .env File

```env
# Django
SECRET_KEY=your-super-secret-key-with-50-chars-minimum
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=ai_attendance_db
DB_USER=postgres
DB_PASSWORD=secure_password_here
DB_HOST=db.yourdomain.com
DB_PORT=5432

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Application
TIME_ZONE=Asia/Riyadh
LANGUAGE_CODE=en-us
USE_I18N=True
USE_TZ=True

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=ai-attendance-system-prod
AWS_S3_REGION_NAME=us-east-1

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Face Recognition
FACE_RECOGNITION_MODEL=hog
MIN_FACE_CONFIDENCE=0.6

# Admin
DJANGO_ADMIN_URL=secure-admin-path-12345/
```

---

**Last Updated**: May 2026
**Django Version**: 5.0+
