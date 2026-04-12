"""Performance optimization configurations for AI Attendance System

This module contains performance settings for caching, database optimization,
and query optimization utilities.
"""

from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class PerformanceOptimizations:
    """Collection of performance optimization utilities."""

    # Cache timeout durations (in seconds)
    CACHE_TIMEOUTS = {
        'model_cache': 3600,          # 1 hour
        'face_encoding_cache': 3600,  # 1 hour
        'student_list_cache': 1800,   # 30 minutes
        'attendance_summary_cache': 600,  # 10 minutes
    }

    # Database query optimization hints
    DB_QUERY_OPTIMIZATION = {
        'select_related_fields': [
            'student__attendance_set',  # Prefetch related attendance
        ],
        'prefetch_related_fields': [
            'attendance_set',  # Prefetch attendance records
        ]
    }

    @staticmethod
    def prefetch_students_with_attendance():
        """Get students with prefetched attendance records (optimized query).
        
        Returns:
            QuerySet: Students with prefetched attendance relations
        """
        from django.db.models import Prefetch
        from app1.models import Student, Attendance
        
        attendance_qs = Attendance.objects.filter(
            check_in_time__isnull=False
        ).select_related('student')
        
        return Student.objects.prefetch_related(
            Prefetch('attendance_set', queryset=attendance_qs)
        )

    @staticmethod
    def cache_view(timeout=None):
        """Decorator to cache view responses.
        
        Args:
            timeout (int): Cache timeout in seconds
            
        Returns:
            function: Decorated view function
        """
        def decorator(view_func):
            @wraps(view_func)
            @cache_page(timeout or PerformanceOptimizations.CACHE_TIMEOUTS['model_cache'])
            def wrapper(*args, **kwargs):
                return view_func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None):
        """Optimize queryset with proper use of select_related and prefetch_related.
        
        Args:
            queryset: Django queryset to optimize
            select_related (list): List of fields for select_related
            prefetch_related (list): List of fields for prefetch_related
            
        Returns:
            QuerySet: Optimized queryset
        """
        if select_related:
            for field in select_related:
                queryset = queryset.select_related(field)
        
        if prefetch_related:
            for field in prefetch_related:
                queryset = queryset.prefetch_related(field)
        
        logger.debug(f"Query optimized with select_related={select_related}, prefetch_related={prefetch_related}")
        return queryset


# Recommended CACHING configuration for settings.py
CACHES_CONFIG = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_py.StrictRedis',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50, 'retry_on_timeout': True},
        },
        'KEY_PREFIX': 'ai_attendance',
        'TIMEOUT': 300,  # Default 5 minutes
    }
}

# Alternative in-memory cache (if Redis not available)
CACHES_CONFIG_MEMORY = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ai-attendance-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        },
        'TIMEOUT': 300,  # Default 5 minutes
    }
}

# Database optimization settings
DATABASE_OPTIMIZATIONS = {
    'CONN_MAX_AGE': 600,  # Close connection after 10 minutes
    'AUTOCOMMIT': True,
    'AUTO_SCHEMA': True,
}

# Query logging and monitoring (development only)
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/ai_attendance.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app1': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
