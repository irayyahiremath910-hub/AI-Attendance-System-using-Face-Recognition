"""
Storage Utility Functions for AI Attendance System

Provides utilities for file validation, optimization, CDN URL generation,
and media file management across local and cloud storage backends.
"""

import os
import mimetypes
from pathlib import Path
from datetime import datetime, timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from decouple import config


class FileValidator:
    """Validator for uploaded files."""
    
    MAX_FILE_SIZE = config('MAX_UPLOAD_SIZE', default=10485760, cast=int)  # 10MB
    ALLOWED_EXTENSIONS = config(
        'ALLOWED_FILE_EXTENSIONS',
        default='jpg,jpeg,png,gif,pdf,doc,docx,txt,xlsx,csv,zip',
        cast=lambda x: [ext.strip().lower() for ext in x.split(',')]
    )
    
    ALLOWED_MIME_TYPES = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
        'zip': 'application/zip',
    }
    
    @staticmethod
    def validate_file(file_obj, max_size=None, allowed_extensions=None):
        """
        Validate uploaded file.
        
        Args:
            file_obj: Uploaded file object
            max_size: Maximum file size in bytes
            allowed_extensions: List of allowed extensions
            
        Raises:
            ValidationError: If file is invalid
        """
        max_size = max_size or FileValidator.MAX_FILE_SIZE
        allowed_extensions = allowed_extensions or FileValidator.ALLOWED_EXTENSIONS
        
        # Check file size
        if file_obj.size > max_size:
            raise ValidationError(
                f'File size {file_obj.size / (1024*1024):.2f}MB exceeds maximum {max_size / (1024*1024):.2f}MB'
            )
        
        # Check file extension
        file_ext = file_obj.name.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationError(
                f'File type .{file_ext} not allowed. Allowed types: {", ".join(allowed_extensions)}'
            )
        
        # Check MIME type if available
        mime_type = FileValidator.get_safe_mime_type(file_obj)
        if not FileValidator.is_safe_mime_type(file_ext, mime_type):
            raise ValidationError(f'Invalid file content for extension .{file_ext}')
    
    @staticmethod
    def validate_image(image_obj, max_size=None):
        """
        Validate image file.
        
        Args:
            image_obj: Image file object
            max_size: Maximum file size in bytes
            
        Raises:
            ValidationError: If image is invalid
        """
        image_extensions = ['jpg', 'jpeg', 'png', 'gif']
        FileValidator.validate_file(image_obj, max_size, image_extensions)
        
        # Additional image validation
        try:
            from PIL import Image
            img = Image.open(image_obj)
            img.verify()
        except Exception as e:
            raise ValidationError(f'Invalid image file: {str(e)}')
    
    @staticmethod
    def get_safe_mime_type(file_obj):
        """Get MIME type of file."""
        file_obj.seek(0)
        mime_type = mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'
        return mime_type
    
    @staticmethod
    def is_safe_mime_type(extension, mime_type):
        """Check if MIME type matches extension."""
        allowed_mime = FileValidator.ALLOWED_MIME_TYPES.get(extension)
        return allowed_mime is None or mime_type == allowed_mime or mime_type.startswith(allowed_mime.split('/')[0])


class StorageManager:
    """Manager for storage operations."""
    
    @staticmethod
    def get_media_url(filename):
        """
        Get URL for media file.
        
        Args:
            filename: Path to file relative to MEDIA_ROOT
            
        Returns:
            str: Full URL to media file
        """
        if config('USE_S3', default=False, cast=bool):
            return f"{settings.MEDIA_URL}{filename}"
        elif config('USE_AZURE', default=False, cast=bool):
            return f"{settings.MEDIA_URL}{filename}"
        else:
            return f"{settings.MEDIA_URL}{filename}"
    
    @staticmethod
    def get_static_url(filename):
        """
        Get URL for static file.
        
        Args:
            filename: Path to file relative to STATIC_ROOT
            
        Returns:
            str: Full URL to static file
        """
        return f"{settings.STATIC_URL}{filename}"
    
    @staticmethod
    def get_cdn_url(filename, file_type='media'):
        """
        Get CDN URL for file if configured.
        
        Args:
            filename: Path to file
            file_type: 'media' or 'static'
            
        Returns:
            str: CDN URL or regular URL if CDN not configured
        """
        cdn_url = config('CDN_URL', default='')
        
        if cdn_url:
            if file_type == 'static':
                return f"{cdn_url}/static/{filename}"
            else:
                return f"{cdn_url}/media/{filename}"
        
        if file_type == 'static':
            return StorageManager.get_static_url(filename)
        else:
            return StorageManager.get_media_url(filename)
    
    @staticmethod
    def cleanup_old_files(directory, days=30, dry_run=False):
        """
        Clean up old files from storage.
        
        Args:
            directory: Directory to clean
            days: Delete files older than this many days
            dry_run: If True, don't actually delete files
            
        Returns:
            dict: Summary of cleanup operation
        """
        if config('USE_S3', default=False, cast=bool):
            return StorageManager._cleanup_s3(days, dry_run)
        else:
            return StorageManager._cleanup_local(directory, days, dry_run)
    
    @staticmethod
    def _cleanup_local(directory, days, dry_run):
        """Clean up local filesystem."""
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        freed_space = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_time:
                        size = os.path.getsize(filepath)
                        freed_space += size
                        deleted_count += 1
                        
                        if not dry_run:
                            try:
                                os.remove(filepath)
                            except Exception as e:
                                print(f'Failed to delete {filepath}: {str(e)}')
            
            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'freed_space': freed_space,
                'dry_run': dry_run,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
            }
    
    @staticmethod
    def _cleanup_s3(days, dry_run):
        """Clean up S3 storage."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client('s3')
            bucket = config('AWS_STORAGE_BUCKET_NAME', default='')
            
            cutoff_time = datetime.now(datetime.UTC) - timedelta(days=days)
            deleted_count = 0
            freed_space = 0
            
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_time:
                        freed_space += obj['Size']
                        deleted_count += 1
                        
                        if not dry_run:
                            try:
                                s3_client.delete_object(Bucket=bucket, Key=obj['Key'])
                            except ClientError as e:
                                print(f'Failed to delete {obj["Key"]}: {str(e)}')
            
            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'freed_space': freed_space,
                'dry_run': dry_run,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
            }
    
    @staticmethod
    def get_storage_stats():
        """
        Get storage usage statistics.
        
        Returns:
            dict: Storage statistics
        """
        if config('USE_S3', default=False, cast=bool):
            return StorageManager._get_s3_stats()
        else:
            return StorageManager._get_local_stats()
    
    @staticmethod
    def _get_local_stats():
        """Get local storage statistics."""
        media_root = settings.MEDIA_ROOT
        static_root = settings.STATIC_ROOT
        
        def get_dir_size(path):
            total = 0
            file_count = 0
            if os.path.exists(path):
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total += os.path.getsize(filepath)
                            file_count += 1
                        except OSError:
                            pass
            return total, file_count
        
        media_size, media_count = get_dir_size(media_root)
        static_size, static_count = get_dir_size(static_root)
        
        return {
            'storage_type': 'Local',
            'media': {
                'path': media_root,
                'size_bytes': media_size,
                'size_mb': round(media_size / (1024*1024), 2),
                'file_count': media_count,
            },
            'static': {
                'path': static_root,
                'size_bytes': static_size,
                'size_mb': round(static_size / (1024*1024), 2),
                'file_count': static_count,
            },
            'total_size_mb': round((media_size + static_size) / (1024*1024), 2),
        }
    
    @staticmethod
    def _get_s3_stats():
        """Get S3 storage statistics."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client('s3')
            bucket = config('AWS_STORAGE_BUCKET_NAME', default='')
            
            total_size = 0
            file_count = 0
            
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    total_size += obj['Size']
                    file_count += 1
            
            return {
                'storage_type': 'AWS S3',
                'bucket': bucket,
                'size_bytes': total_size,
                'size_mb': round(total_size / (1024*1024), 2),
                'file_count': file_count,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
            }


def generate_file_hash(file_obj):
    """
    Generate SHA-256 hash of file for duplicate detection.
    
    Args:
        file_obj: File object to hash
        
    Returns:
        str: Hex digest of SHA-256 hash
    """
    import hashlib
    
    file_obj.seek(0)
    hash_sha256 = hashlib.sha256()
    
    for chunk in file_obj.chunks():
        hash_sha256.update(chunk)
    
    return hash_sha256.hexdigest()


def optimize_image(image_obj, max_width=2000, max_height=2000, quality=85):
    """
    Optimize image by resizing and compressing.
    
    Args:
        image_obj: PIL Image object
        max_width: Maximum image width
        max_height: Maximum image height
        quality: JPEG quality (1-95)
        
    Returns:
        PIL.Image: Optimized image
    """
    try:
        from PIL import Image
        
        # Resize if needed
        image_obj.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        return image_obj
    except Exception as e:
        print(f'Image optimization failed: {str(e)}')
        return image_obj
