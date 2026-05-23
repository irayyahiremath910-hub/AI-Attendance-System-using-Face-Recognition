"""
Storage Configuration Module for AI Attendance System

Handles configuration for file storage backends (Local, AWS S3, Azure Blob Storage).
Supports dynamic switching between storage providers based on environment variables.
"""

import os
from pathlib import Path
from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


class StorageConfig:
    """Storage configuration handler for multiple backends."""
    
    @staticmethod
    def get_storage_backend():
        """
        Get the configured storage backend.
        
        Returns:
            str: Storage backend class path
        """
        use_s3 = config('USE_S3', default=False, cast=bool)
        use_azure = config('USE_AZURE', default=False, cast=bool)
        
        if use_s3:
            return 'storages.backends.s3boto3.S3Boto3Storage'
        elif use_azure:
            return 'storages.backends.azure_storage.AzureStorage'
        else:
            return 'django.core.files.storage.FileSystemStorage'
    
    @staticmethod
    def get_default_file_storage():
        """Get default file storage for media files."""
        backend = StorageConfig.get_storage_backend()
        return backend
    
    @staticmethod
    def get_static_file_storage():
        """Get static files storage backend."""
        use_s3 = config('USE_S3', default=False, cast=bool)
        
        if use_s3:
            return 'storages.backends.s3boto3.S3StaticStorage'
        else:
            return 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'


def get_s3_config():
    """
    Get AWS S3 configuration.
    
    Returns:
        dict: S3 configuration settings
    """
    if not config('USE_S3', default=False, cast=bool):
        return None
    
    access_key = config('AWS_ACCESS_KEY_ID', default='')
    secret_key = config('AWS_SECRET_ACCESS_KEY', default='')
    bucket = config('AWS_STORAGE_BUCKET_NAME', default='')
    
    if not all([access_key, secret_key, bucket]):
        raise ImproperlyConfigured(
            'AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME '
            'must be set when USE_S3=True'
        )
    
    return {
        'access_key_id': access_key,
        'secret_access_key': secret_key,
        'storage_bucket_name': bucket,
        'region_name': config('AWS_S3_REGION_NAME', default='us-east-1'),
        'custom_domain': config('AWS_S3_CUSTOM_DOMAIN', default=f'{bucket}.s3.amazonaws.com'),
        'default_acl': config('AWS_S3_DEFAULT_ACL', default='public-read'),
    }


def get_azure_config():
    """
    Get Azure Blob Storage configuration.
    
    Returns:
        dict: Azure configuration settings
    """
    if not config('USE_AZURE', default=False, cast=bool):
        return None
    
    account_name = config('AZURE_ACCOUNT_NAME', default='')
    account_key = config('AZURE_ACCOUNT_KEY', default='')
    container = config('AZURE_CONTAINER', default='media')
    
    if not all([account_name, account_key]):
        raise ImproperlyConfigured(
            'AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY must be set when USE_AZURE=True'
        )
    
    return {
        'account_name': account_name,
        'account_key': account_key,
        'azure_container': container,
        'account_url': f'https://{account_name}.blob.core.windows.net',
    }


def get_storage_info():
    """
    Get human-readable storage information for logging/debugging.
    
    Returns:
        dict: Storage information without sensitive credentials
    """
    use_s3 = config('USE_S3', default=False, cast=bool)
    use_azure = config('USE_AZURE', default=False, cast=bool)
    
    info = {
        'backend': 'Unknown',
        'type': 'Local',
    }
    
    if use_s3:
        info['backend'] = 'AWS S3'
        info['type'] = 'Cloud'
        info['bucket'] = config('AWS_STORAGE_BUCKET_NAME', default='Not set')
        info['region'] = config('AWS_S3_REGION_NAME', default='us-east-1')
    elif use_azure:
        info['backend'] = 'Azure Blob Storage'
        info['type'] = 'Cloud'
        info['account'] = config('AZURE_ACCOUNT_NAME', default='Not set')
        info['container'] = config('AZURE_CONTAINER', default='media')
    else:
        info['backend'] = 'Local File System'
        info['type'] = 'Local'
        info['media_root'] = str(BASE_DIR / config('MEDIA_ROOT', default='media/'))
        info['static_root'] = str(BASE_DIR / config('STATIC_ROOT', default='staticfiles/'))
    
    return info


# File upload configuration
FILE_UPLOAD_MAX_SIZE = config('MAX_UPLOAD_SIZE', default=10485760, cast=int)  # 10MB
FILE_UPLOAD_ALLOWED_EXTENSIONS = config(
    'ALLOWED_FILE_EXTENSIONS',
    default='jpg,jpeg,png,gif,pdf,doc,docx,txt,xlsx,csv,zip',
    cast=lambda x: [ext.strip().lower() for ext in x.split(',')]
)

# Content type mapping for file validation
ALLOWED_MIME_TYPES = {
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'png': ['image/png'],
    'gif': ['image/gif'],
    'pdf': ['application/pdf'],
    'doc': ['application/msword'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'txt': ['text/plain'],
    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'csv': ['text/csv'],
    'zip': ['application/zip'],
}

# Cache control headers for different file types
CACHE_CONTROL_STATIC = 'public, max-age=31536000, immutable'  # 1 year for static files
CACHE_CONTROL_MEDIA = 'public, max-age=3600'  # 1 hour for media files


def get_upload_directory(instance, filename):
    """
    Generate upload directory path based on model and timestamp.
    
    Usage:
        class MyModel(models.Model):
            file = models.FileField(upload_to=get_upload_directory)
    
    Args:
        instance: Model instance
        filename: Original filename
        
    Returns:
        str: Upload directory path
    """
    from datetime import datetime
    
    model_name = instance.__class__.__name__.lower()
    timestamp = datetime.now().strftime('%Y/%m/%d')
    
    return f'{model_name}/{timestamp}/{filename}'


def get_image_upload_directory(instance, filename):
    """Generate upload directory path for images."""
    from datetime import datetime
    
    model_name = instance.__class__.__name__.lower()
    timestamp = datetime.now().strftime('%Y/%m/%d')
    
    return f'images/{model_name}/{timestamp}/{filename}'


def get_document_upload_directory(instance, filename):
    """Generate upload directory path for documents."""
    from datetime import datetime
    
    model_name = instance.__class__.__name__.lower()
    timestamp = datetime.now().strftime('%Y/%m/%d')
    
    return f'documents/{model_name}/{timestamp}/{filename}'


# Storage optimization settings
STORAGES = {
    'default': {
        'BACKEND': StorageConfig.get_storage_backend(),
    },
    'staticfiles': {
        'BACKEND': StorageConfig.get_static_file_storage(),
    },
}
