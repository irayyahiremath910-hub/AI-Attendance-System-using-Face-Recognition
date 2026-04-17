"""
Caching layer and performance optimization utilities
Implements Redis caching, query optimization, and performance monitoring
"""

from django.core.cache import cache
from django.views.decorators.cache import cache_page
from functools import wraps
from django.db.models import Q, Prefetch
from app1.models import Student, Attendance
import hashlib
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# Cache timeout constants
CACHE_TIMEOUT_SHORT = 5 * 60  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 30 * 60  # 30 minutes
CACHE_TIMEOUT_LONG = 24 * 60 * 60  # 24 hours


class CacheService:
    """Service for managing application cache"""

    @staticmethod
    def get_cache_key(prefix: str, *args) -> str:
        """Generate consistent cache key"""
        key_str = f"{prefix}:" + ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()

    @staticmethod
    def get_or_set(key: str, callable_func, timeout=CACHE_TIMEOUT_MEDIUM):
        """Get value from cache or set it"""
        value = cache.get(key)

        if value is None:
            value = callable_func()
            cache.set(key, value, timeout)

        return value

    @staticmethod
    def invalidate_cache(pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            # For Redis backend
            from django.core.cache import cache as redis_cache

            if hasattr(redis_cache, 'delete_pattern'):
                redis_cache.delete_pattern(f"*{pattern}*")
            else:
                logger.warning(f"Cache backend doesn't support pattern deletion for {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")

    @staticmethod
    def clear_all_cache():
        """Clear entire cache"""
        try:
            cache.clear()
            logger.info("All cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")


class StudentCache:
    """Caching for student-related queries"""

    CACHE_PREFIX = "student"

    @staticmethod
    def get_student_by_id(student_id: int):
        """Get student with caching"""
        key = CacheService.get_cache_key(StudentCache.CACHE_PREFIX, student_id)

        def fetch():
            try:
                return Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return None

        return CacheService.get_or_set(key, fetch, CACHE_TIMEOUT_LONG)

    @staticmethod
    def get_all_authorized_students():
        """Get all authorized students with caching"""
        key = CacheService.get_cache_key(StudentCache.CACHE_PREFIX, "authorized_all")

        def fetch():
            return list(
                Student.objects.filter(authorized=True).values_list('id', 'name', 'email')
            )

        return CacheService.get_or_set(key, fetch, CACHE_TIMEOUT_MEDIUM)

    @staticmethod
    def get_students_by_class(class_name: str):
        """Get students in a class with caching"""
        key = CacheService.get_cache_key(StudentCache.CACHE_PREFIX, "class", class_name)

        def fetch():
            return list(
                Student.objects.filter(
                    student_class__icontains=class_name
                ).values('id', 'name', 'roll_number', 'email')
            )

        return CacheService.get_or_set(key, fetch, CACHE_TIMEOUT_MEDIUM)

    @staticmethod
    def invalidate_student_cache(student_id: int):
        """Invalidate student cache"""
        key = CacheService.get_cache_key(StudentCache.CACHE_PREFIX, student_id)
        cache.delete(key)
        CacheService.invalidate_cache(f"{StudentCache.CACHE_PREFIX}:*")

    @staticmethod
    def refresh_class_cache(class_name: str):
        """Refresh class cache"""
        key = CacheService.get_cache_key(StudentCache.CACHE_PREFIX, "class", class_name)
        cache.delete(key)


class AttendanceCache:
    """Caching for attendance-related queries"""

    CACHE_PREFIX = "attendance"

    @staticmethod
    def get_today_attendance():
        """Get today's attendance with caching"""
        from datetime import date

        key = CacheService.get_cache_key(AttendanceCache.CACHE_PREFIX, "today", date.today())

        def fetch():
            return list(
                Attendance.objects.filter(date=date.today()).select_related('student')
            )

        return CacheService.get_or_set(key, fetch, CACHE_TIMEOUT_SHORT)

    @staticmethod
    def get_student_attendance_summary(student_id: int, days: int = 30):
        """Get student attendance summary with caching"""
        from datetime import date, timedelta

        key = CacheService.get_cache_key(
            AttendanceCache.CACHE_PREFIX,
            "summary",
            student_id,
            days
        )

        def fetch():
            start_date = date.today() - timedelta(days=days)
            records = Attendance.objects.filter(
                student_id=student_id,
                date__gte=start_date
            )

            return {
                'total': records.count(),
                'present': records.filter(status='Present').count(),
                'absent': records.filter(status='Absent').count(),
                'late': records.filter(status='Late').count()
            }

        return CacheService.get_or_set(key, fetch, CACHE_TIMEOUT_MEDIUM)

    @staticmethod
    def get_class_statistics(class_name: str):
        """Get class attendance statistics with caching"""
        key = CacheService.get_cache_key(
            AttendanceCache.CACHE_PREFIX,
            "class_stats",
            class_name
        )

        def fetch():
            students = Student.objects.filter(student_class__icontains=class_name)
            student_ids = list(students.values_list('id', flat=True))

            attendance = Attendance.objects.filter(student_id__in=student_ids)

            return {
                'total_students': len(student_ids),
                'total_records': attendance.count(),
                'present_count': attendance.filter(status='Present').count(),
                'absent_count': attendance.filter(status='Absent').count(),
                'late_count': attendance.filter(status='Late').count(),
                'average_attendance_percent': round(
                    (attendance.filter(status='Present').count() / attendance.count() * 100)
                    if attendance.count() > 0 else 0
                )
            }

        return CacheService.get_or_set(key, fetch, CACHE_TIMEOUT_MEDIUM)

    @staticmethod
    def invalidate_attendance_cache():
        """Invalidate all attendance cache"""
        CacheService.invalidate_cache(f"{AttendanceCache.CACHE_PREFIX}:*")


def cache_view_results(timeout=CACHE_TIMEOUT_MEDIUM):
    """Decorator to cache view results"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            cache_key = CacheService.get_cache_key(
                view_func.__name__,
                request.user.id,
                request.get_full_path(),
                request.method
            )

            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            response = view_func(request, *args, **kwargs)

            if response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


class QueryOptimizer:
    """Optimize database queries using select_related and prefetch_related"""

    @staticmethod
    def optimize_student_queries(queryset):
        """Optimize student queries"""
        return queryset.select_related().prefetch_related('attendance_set')

    @staticmethod
    def optimize_attendance_queries(queryset):
        """Optimize attendance queries"""
        return queryset.select_related('student')

    @staticmethod
    def get_optimized_students_list():
        """Get optimized list of all students"""
        return QueryOptimizer.optimize_student_queries(
            Student.objects.all()
        )

    @staticmethod
    def get_optimized_attendance_list():
        """Get optimized list of all attendance records"""
        return QueryOptimizer.optimize_attendance_queries(
            Attendance.objects.all()
        )


class PerformanceMonitor:
    """Monitor and log performance metrics"""

    @staticmethod
    def log_query_count(view_name: str):
        """Decorator to log database query count"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(*args, **kwargs):
                from django.db import connection
                from django.test.utils import CaptureQueriesContext

                with CaptureQueriesContext(connection) as ctx:
                    result = view_func(*args, **kwargs)
                    query_count = len(ctx)

                if query_count > 10:
                    logger.warning(
                        f"{view_name} executed {query_count} queries"
                    )
                else:
                    logger.info(f"{view_name} executed {query_count} queries")

                return result

            return wrapper

        return decorator

    @staticmethod
    def log_execution_time(threshold_ms: float = 1000):
        """Decorator to log slow function execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time

                start = time.time()
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000

                if duration_ms > threshold_ms:
                    logger.warning(
                        f"{func.__name__} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(
                        f"{func.__name__} took {duration_ms:.2f}ms"
                    )

                return result

            return wrapper

        return decorator
