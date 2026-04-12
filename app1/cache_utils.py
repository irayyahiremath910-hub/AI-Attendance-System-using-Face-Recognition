"""Cache utilities for the AI Attendance System

Provides helper functions for cache management and optimization.
"""

from django.core.cache import cache
from django.views.decorators.cache import cache_page
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Centralized cache management for the application."""

    # Cache key prefixes
    PREFIXES = {
        'face_encoding': 'face_encoding:',
        'student': 'student:',
        'attendance': 'attendance:',
        'camera': 'camera:',
        'summary': 'summary:',
    }

    # Default cache timeouts
    TIMEOUTS = {
        'face_encoding': 3600,        # 1 hour
        'student': 1800,              # 30 minutes
        'attendance': 600,            # 10 minutes
        'camera': 3600,               # 1 hour
        'summary': 300,               # 5 minutes
    }

    @staticmethod
    def get_key(prefix, identifier):
        """Generate a cache key from prefix and identifier.
        
        Args:
            prefix (str): Cache key prefix
            identifier: Unique identifier
            
        Returns:
            str: Full cache key
        """
        return f"{prefix}{identifier}"

    @staticmethod
    def set_student_cache(student_id, data, timeout=None):
        """Cache student data.
        
        Args:
            student_id: Student primary key
            data: Data to cache
            timeout: Cache timeout in seconds
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['student'], student_id)
        timeout = timeout or CacheManager.TIMEOUTS['student']
        cache.set(key, data, timeout)
        logger.debug(f"Student {student_id} cached for {timeout}s")

    @staticmethod
    def get_student_cache(student_id):
        """Retrieve cached student data.
        
        Args:
            student_id: Student primary key
            
        Returns:
            Cached data or None
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['student'], student_id)
        return cache.get(key)

    @staticmethod
    def delete_student_cache(student_id):
        """Delete cached student data.
        
        Args:
            student_id: Student primary key
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['student'], student_id)
        cache.delete(key)
        logger.debug(f"Student {student_id} cache cleared")

    @staticmethod
    def set_attendance_cache(attendance_id, data, timeout=None):
        """Cache attendance data.
        
        Args:
            attendance_id: Attendance primary key
            data: Data to cache
            timeout: Cache timeout in seconds
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['attendance'], attendance_id)
        timeout = timeout or CacheManager.TIMEOUTS['attendance']
        cache.set(key, data, timeout)
        logger.debug(f"Attendance {attendance_id} cached for {timeout}s")

    @staticmethod
    def get_attendance_cache(attendance_id):
        """Retrieve cached attendance data.
        
        Args:
            attendance_id: Attendance primary key
            
        Returns:
            Cached data or None
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['attendance'], attendance_id)
        return cache.get(key)

    @staticmethod
    def set_face_encoding_cache(encoding_key, encodings, names, timeout=None):
        """Cache face encodings.
        
        Args:
            encoding_key: Identifier for encoding set
            encodings: List of face encodings
            names: List of corresponding names
            timeout: Cache timeout in seconds
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['face_encoding'], encoding_key)
        timeout = timeout or CacheManager.TIMEOUTS['face_encoding']
        cache.set(key, {'encodings': encodings, 'names': names}, timeout)
        logger.debug(f"Face encodings cached with key {encoding_key} for {timeout}s")

    @staticmethod
    def get_face_encoding_cache(encoding_key):
        """Retrieve cached face encodings.
        
        Args:
            encoding_key: Identifier for encoding set
            
        Returns:
            Dict with 'encodings' and 'names' or None
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['face_encoding'], encoding_key)
        return cache.get(key)

    @staticmethod
    def set_summary_cache(summary_key, data, timeout=None):
        """Cache summary data.
        
        Args:
            summary_key: Identifier for summary
            data: Summary data to cache
            timeout: Cache timeout in seconds
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['summary'], summary_key)
        timeout = timeout or CacheManager.TIMEOUTS['summary']
        cache.set(key, data, timeout)
        logger.debug(f"Summary {summary_key} cached for {timeout}s")

    @staticmethod
    def get_summary_cache(summary_key):
        """Retrieve cached summary data.
        
        Args:
            summary_key: Identifier for summary
            
        Returns:
            Cached summary or None
        """
        key = CacheManager.get_key(CacheManager.PREFIXES['summary'], summary_key)
        return cache.get(key)

    @staticmethod
    def clear_all_cache():
        """Clear all application cache."""
        cache.clear()
        logger.info("All application cache cleared")

    @staticmethod
    def get_cache_stats():
        """Get cache statistics.
        
        Returns:
            dict: Cache statistics
        """
        try:
            if hasattr(cache, 'get_stats'):
                return cache.get_stats()
            return {'status': 'Cache backend does not support statistics'}
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}


def cached_api_response(timeout=300):
    """Decorator for caching API responses.
    
    Args:
        timeout (int): Cache timeout in seconds
        
    Returns:
        function: Decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key from request path and method
            cache_key = f"api:{request.method}:{request.path}:{request.GET.urlencode()}"
            
            # Try to get from cache
            response = cache.get(cache_key)
            if response:
                logger.debug(f"API response served from cache: {cache_key}")
                return response
            
            # Call the view function
            response = view_func(request, *args, **kwargs)
            
            # Cache the response if it's successful
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)
                logger.debug(f"API response cached: {cache_key} for {timeout}s")
            
            return response
        return wrapper
    return decorator
