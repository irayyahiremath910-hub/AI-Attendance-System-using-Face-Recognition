## Static Files & Media Storage Configuration

This document provides comprehensive guidance on configuring and managing static files and media storage for the AI Attendance System.

---

## Table of Contents

1. [Overview](#overview)
2. [Static Files Configuration](#static-files-configuration)
3. [Media Files Configuration](#media-files-configuration)
4. [Cloud Storage Setup](#cloud-storage-setup)
5. [File Upload Limits](#file-upload-limits)
6. [CDN Configuration](#cdn-configuration)
7. [Local Development Setup](#local-development-setup)
8. [Production Deployment](#production-deployment)
9. [Storage Utilities](#storage-utilities)
10. [Maintenance & Cleanup](#maintenance--cleanup)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Attendance System supports three storage backends:

1. **Local File System** - Development and testing (SQLite)
2. **AWS S3** - Production cloud storage
3. **Azure Blob Storage** - Alternative cloud storage

Static files (CSS, JavaScript, images) and media files (user uploads) are managed separately for optimal performance and scalability.

### File Structure

```
Project101/
├── settings.py              # Storage configuration
├── storage_config.py        # Storage backend selection
└── db_config.py            # Database configuration

app1/
└── storage_utils.py        # File validation and utilities

media/                       # Media uploads (local)
staticfiles/                # Collected static files (local)
static/                     # Static file source (local)
```

---

## Static Files Configuration

### Development Setup

Static files are served directly from the `static/` directory:

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static/')]
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
```

### Collecting Static Files

Before deployment, collect all static files:

```bash
python manage.py collectstatic --noinput
```

This command:
- Gathers all static files from `STATICFILES_DIRS`
- Processes them through storage backend
- Generates versioned filenames for cache busting
- Creates manifest for tracking

### Directory Structure

```
project/
├── static/              # Source static files
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
│       └── logo.png
└── staticfiles/         # Collected and processed files
    ├── css/
    │   └── style.abc123.css
    ├── js/
    │   └── app.def456.js
    └── images/
        └── logo.xyz789.png
```

---

## Media Files Configuration

### Local Storage

Media files are stored in `media/` directory:

```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
```

### Upload Handling

Configure file upload limits:

```bash
# .env
MAX_UPLOAD_SIZE=10485760          # 10MB in bytes
ALLOWED_FILE_EXTENSIONS=jpg,jpeg,png,gif,pdf,doc,docx,txt,xlsx,csv,zip
```

### Organizing Uploads

Use model-based organization:

```python
# models.py
from app1.storage_utils import get_image_upload_directory

class StudentProfile(models.Model):
    photo = models.ImageField(
        upload_to=get_image_upload_directory,
        help_text='Student ID photo'
    )
```

This creates structure:
```
media/
└── images/
    └── studentprofile/
        └── 2024/05/15/
            └── photo.jpg
```

---

## Cloud Storage Setup

### AWS S3 Configuration

#### Step 1: Create S3 Bucket

```bash
# AWS Console or AWS CLI
aws s3 mb s3://my-ai-attendance-bucket --region us-east-1
```

#### Step 2: Create IAM User

Create IAM user with S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-ai-attendance-bucket",
        "arn:aws:s3:::my-ai-attendance-bucket/*"
      ]
    }
  ]
}
```

#### Step 3: Configure Environment

```bash
# .env
USE_S3=True
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=my-ai-attendance-bucket
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=my-ai-attendance-bucket.s3.amazonaws.com
AWS_DEFAULT_ACL=public-read
```

#### Step 4: Install Dependencies

```bash
pip install django-storages boto3
```

### Azure Blob Storage Configuration

#### Step 1: Create Storage Account

```bash
# Azure CLI
az storage account create \
  --name mystorageaccount \
  --resource-group myresourcegroup \
  --location eastus
```

#### Step 2: Create Container

```bash
az storage container create \
  --name media \
  --account-name mystorageaccount
```

#### Step 3: Configure Environment

```bash
# .env
USE_AZURE=True
AZURE_ACCOUNT_NAME=mystorageaccount
AZURE_ACCOUNT_KEY=your_account_key
AZURE_CONTAINER=media
```

---

## File Upload Limits

### Configuration

```bash
# .env
MAX_UPLOAD_SIZE=10485760                    # 10MB
ALLOWED_FILE_EXTENSIONS=jpg,jpeg,png,gif,pdf,doc,docx,txt,xlsx,csv,zip
```

### Validation

File validation is automatic through `FileValidator`:

```python
from app1.storage_utils import FileValidator

# Validate file
try:
    FileValidator.validate_file(uploaded_file)
except ValidationError as e:
    print(f"Invalid file: {e}")

# Validate image specifically
try:
    FileValidator.validate_image(uploaded_image)
except ValidationError as e:
    print(f"Invalid image: {e}")
```

### Supported File Types

| Extension | MIME Type | Use Case |
|-----------|-----------|----------|
| jpg, jpeg | image/jpeg | Student photos |
| png | image/png | UI images |
| gif | image/gif | Animations |
| pdf | application/pdf | Documents |
| doc, docx | application/msword* | Word documents |
| txt | text/plain | Text files |
| xlsx | application/vnd.* | Excel spreadsheets |
| csv | text/csv | Data imports |
| zip | application/zip | Archive files |

---

## CDN Configuration

### CloudFront Setup (AWS)

#### Step 1: Create Distribution

```bash
# AWS Console: CloudFront > Create Distribution
# Origin: S3 bucket (my-ai-attendance-bucket.s3.amazonaws.com)
# Default cache behavior: Use default settings
# Compression: Enable
```

#### Step 2: Configure Django

```bash
# .env
USE_S3=True
CDN_URL=https://d123456.cloudfront.net

# Get CDN URLs
from app1.storage_utils import StorageManager
cdn_url = StorageManager.get_cdn_url('images/student/photo.jpg')
# Returns: https://d123456.cloudfront.net/media/images/student/photo.jpg
```

### Cache Control

Set appropriate cache headers:

```python
# Project101/settings.py
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=31536000, immutable',  # 1 year for static
}
```

---

## Local Development Setup

### Step 1: Create Directories

```bash
mkdir -p static media
mkdir -p static/css static/js static/images
```

### Step 2: Configure Settings

```bash
# .env
USE_S3=False
USE_AZURE=False
STATIC_URL=/static/
MEDIA_URL=/media/
MEDIA_ROOT=media/
STATIC_ROOT=staticfiles/
```

### Step 3: Run Development Server

```bash
python manage.py runserver
```

Access files at:
- Static: http://localhost:8000/static/
- Media: http://localhost:8000/media/

---

## Production Deployment

### WhiteNoise Setup

For efficient static file serving in production:

```bash
pip install whitenoise
```

Add to middleware:

```python
# settings.py
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # First
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### S3 Deployment Checklist

- [ ] S3 bucket created and configured
- [ ] IAM user created with appropriate permissions
- [ ] Credentials stored securely in .env
- [ ] django-storages installed
- [ ] USE_S3=True in production .env
- [ ] `python manage.py collectstatic --noinput` run
- [ ] Files uploaded to S3 successfully
- [ ] STATIC_URL and MEDIA_URL point to S3
- [ ] CloudFront distribution created (if using CDN)
- [ ] CDN cache invalidation configured

### Environment Variables

```bash
# Production .env
USE_S3=True
AWS_ACCESS_KEY_ID=prod_access_key
AWS_SECRET_ACCESS_KEY=prod_secret_key
AWS_STORAGE_BUCKET_NAME=production-bucket
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=production-bucket.s3.amazonaws.com
CDN_URL=https://cdn.yourdomain.com
```

---

## Storage Utilities

### File Validation

```python
from app1.storage_utils import FileValidator

# Validate file
FileValidator.validate_file(file_obj)

# Validate image with size checking
FileValidator.validate_image(image_obj, max_size=5242880)  # 5MB

# Get MIME type
mime = FileValidator.get_safe_mime_type(file_obj)

# Check MIME type safety
is_safe = FileValidator.is_safe_mime_type('jpg', 'image/jpeg')
```

### Storage Management

```python
from app1.storage_utils import StorageManager

# Get media URL
url = StorageManager.get_media_url('student/photo.jpg')

# Get CDN URL
cdn_url = StorageManager.get_cdn_url('student/photo.jpg', file_type='media')

# Get storage statistics
stats = StorageManager.get_storage_stats()
# {
#   'storage_type': 'AWS S3',
#   'size_mb': 1024.5,
#   'file_count': 15000
# }
```

### File Hash Generation

```python
from app1.storage_utils import generate_file_hash

# Generate SHA-256 hash
file_hash = generate_file_hash(file_obj)
# Returns: 'abc123def456...'
```

### Image Optimization

```python
from app1.storage_utils import optimize_image
from PIL import Image

img = Image.open('photo.jpg')
optimized = optimize_image(img, max_width=1920, max_height=1080, quality=85)
```

---

## Maintenance & Cleanup

### Remove Old Files

```bash
# Python shell
from app1.storage_utils import StorageManager

# Dry run - see what would be deleted
result = StorageManager.cleanup_old_files('media/', days=30, dry_run=True)

# Actually delete files older than 30 days
result = StorageManager.cleanup_old_files('media/', days=30, dry_run=False)
```

### Check Storage Usage

```bash
from app1.storage_utils import StorageManager

stats = StorageManager.get_storage_stats()

if stats.get('storage_type') == 'Local':
    print(f"Media: {stats['media']['size_mb']}MB")
    print(f"Static: {stats['static']['size_mb']}MB")
    print(f"Total: {stats['total_size_mb']}MB")
elif stats.get('storage_type') == 'AWS S3':
    print(f"S3 Bucket: {stats['bucket']}")
    print(f"Total Size: {stats['size_mb']}MB")
    print(f"Files: {stats['file_count']}")
```

### Scheduled Cleanup

Create management command for periodic cleanup:

```python
# app1/management/commands/cleanup_old_files.py
from django.core.management.base import BaseCommand
from app1.storage_utils import StorageManager
from django.conf import settings

class Command(BaseCommand):
    help = 'Clean up old files from storage'
    
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        result = StorageManager.cleanup_old_files(
            settings.MEDIA_ROOT,
            days=days,
            dry_run=dry_run
        )
        
        if result['status'] == 'success':
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {result['deleted_count']} files, "
                    f"freed {result['freed_space'] / (1024*1024):.2f}MB"
                )
            )
```

Run periodically:

```bash
# Daily cleanup (cron)
0 2 * * * cd /path/to/project && python manage.py cleanup_old_files --days 30

# Or use Celery for periodic tasks
from celery import shared_task
from app1.storage_utils import StorageManager
from django.conf import settings

@shared_task
def cleanup_old_storage():
    return StorageManager.cleanup_old_files(settings.MEDIA_ROOT, days=30)
```

---

## Troubleshooting

### Issue: Static files not loading in production

**Solution:**
```bash
# Re-collect static files
python manage.py collectstatic --clear --noinput

# Verify STATIC_URL and STATIC_ROOT in settings
# Ensure web server (Nginx/Apache) serves from STATIC_ROOT
```

### Issue: S3 permission denied errors

**Solution:**
```bash
# Check IAM policy includes required actions:
# s3:GetObject
# s3:PutObject
# s3:DeleteObject
# s3:ListBucket

# Verify credentials are correct
# Check AWS_STORAGE_BUCKET_NAME matches bucket name
```

### Issue: File uploads failing with validation errors

**Solution:**
```python
from app1.storage_utils import FileValidator

# Check file size
print(f"File size: {file.size} bytes")
print(f"Max size: {FileValidator.MAX_FILE_SIZE} bytes")

# Check extension
ext = file.name.split('.')[-1].lower()
print(f"Extension: {ext}")
print(f"Allowed: {FileValidator.ALLOWED_EXTENSIONS}")

# Validate manually
try:
    FileValidator.validate_file(file)
except ValidationError as e:
    print(f"Error: {e}")
```

### Issue: CloudFront cache not updating

**Solution:**
```bash
# Invalidate cache after updates
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"

# Or configure Django to auto-invalidate
# (Requires boto3 and additional configuration)
```

### Issue: High storage costs with S3

**Solution:**
- Implement file cleanup policies (see Maintenance section)
- Use S3 Lifecycle policies for automatic archival
- Compress images before upload
- Consider S3 Intelligent-Tiering
- Monitor CloudFront cache hit ratios

---

## Additional Resources

- [Django Static Files Documentation](https://docs.djangoproject.com/en/5.0/howto/static-files/)
- [Django File Upload Documentation](https://docs.djangoproject.com/en/5.0/topics/http/file-uploads/)
- [django-storages Documentation](https://django-storages.readthedocs.io/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Azure Blob Storage Documentation](https://learn.microsoft.com/en-us/azure/storage/blobs/)

---

## Support

For issues or questions regarding storage configuration:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review storage configuration in `Project101/storage_config.py`
3. Check Django settings in `Project101/settings.py`
4. Consult utility functions in `app1/storage_utils.py`
5. Review environment variables in `.env` file
