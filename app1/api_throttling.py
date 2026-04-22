"""Rate Limiting and Throttling Configuration - Day 8

This module configures rate limiting and throttling to prevent abuse
and ensure fair usage of the API.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, SimpleRateThrottle
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class StandardUserThrottle(UserRateThrottle):
    """Standard rate limit for authenticated users."""
    scope = 'standard_user'
    # Configuration goes in settings.py:
    # REST_FRAMEWORK['THROTTLE_RATES'] = {'standard_user': '1000/hour'}


class PremiumUserThrottle(UserRateThrottle):
    """Premium rate limit for authenticated users."""
    scope = 'premium_user'
    # Configuration: 5000/hour


class StandardAnonThrottle(AnonRateThrottle):
    """Standard rate limit for anonymous users."""
    scope = 'standard_anon'
    # Configuration: 100/hour


class BulkOperationThrottle(SimpleRateThrottle):
    """Stricter throttle for bulk operations to prevent abuse."""
    scope = 'bulk_operations'
    # Configuration: 50/hour


class BurstThrottle(SimpleRateThrottle):
    """Allow burst traffic but limit sustained high rate."""
    scope = 'burst'
    # Configuration: 10/minute


class AdminThrottle(UserRateThrottle):
    """Higher limit for admin operations."""
    scope = 'admin'
    # Configuration: 10000/hour


class AnalyticsThrottle(SimpleRateThrottle):
    """Moderate limit for analytics queries."""
    scope = 'analytics'
    # Configuration: 500/hour


class ThrottlingConfiguration:
    """Centralized throttling configuration."""
    
    # Throttle classes to use
    DEFAULT_THROTTLE_CLASSES = [
        'app1.api_throttling.StandardUserThrottle',
        'app1.api_throttling.StandardAnonThrottle',
    ]
    
    # Throttle rates (to be added to settings.py)
    THROTTLE_RATES = {
        'standard_user': '1000/hour',
        'premium_user': '5000/hour',
        'standard_anon': '100/hour',
        'bulk_operations': '50/hour',
        'burst': '10/minute',
        'admin': '10000/hour',
        'analytics': '500/hour',
    }
    
    # Endpoint-specific throttling configuration
    ENDPOINT_THROTTLES = {
        'students': {
            'list': ['standard_user', 'standard_anon'],
            'create': ['standard_user', 'standard_anon'],
            'bulk_authorize': ['bulk_operations'],
            'bulk_delete': ['bulk_operations'],
            'send_bulk_reminders': ['bulk_operations'],
        },
        'attendance': {
            'list': ['standard_user', 'standard_anon'],
            'bulk_checkout': ['bulk_operations'],
            'bulk_delete': ['bulk_operations'],
            'check_in': ['standard_user', 'standard_anon'],
            'check_out': ['standard_user', 'standard_anon'],
        },
        'analytics': {
            'list': ['analytics'],
            'student': ['analytics'],
            'departments': ['analytics'],
        }
    }


class RateLimitExceededResponse:
    """Handle rate limit exceeded scenarios."""
    
    @staticmethod
    def get_response():
        """Get rate limit exceeded response."""
        return Response(
            {
                'detail': 'Rate limit exceeded. Please try again later.',
                'error_code': 'THROTTLED',
                'error_type': 'RateLimitExceeded'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )


class ThrottlingMiddleware:
    """Middleware for custom throttling logic."""
    
    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
        logger.info("ThrottlingMiddleware initialized")
    
    def __call__(self, request):
        """Process request."""
        # Add custom throttling logic here if needed
        response = self.get_response(request)
        
        # Add rate limit headers to response
        if hasattr(request, 'throttle_waits'):
            for throttle in request.throttle_waits:
                response['X-RateLimit-Remaining'] = str(throttle.throttle_success_count)
                response['X-RateLimit-Reset'] = str(throttle.wait())
        
        return response


# Throttle configuration for different endpoints
BULK_OPERATION_THROTTLE_CONFIG = {
    'scopes': ['bulk_operations'],
    'rate': '50/hour',
    'max_requests_per_batch': 100,
    'description': 'Limited to 50 bulk operations per hour'
}

ANALYTICS_THROTTLE_CONFIG = {
    'scopes': ['analytics'],
    'rate': '500/hour',
    'description': 'Limited to 500 analytics queries per hour'
}

STANDARD_THROTTLE_CONFIG = {
    'authenticated': {
        'scopes': ['standard_user'],
        'rate': '1000/hour',
        'description': 'Limited to 1000 requests per hour'
    },
    'anonymous': {
        'scopes': ['standard_anon'],
        'rate': '100/hour',
        'description': 'Limited to 100 requests per hour'
    }
}


def get_throttle_classes_for_action(view_name, action):
    """Get appropriate throttle classes for a given action."""
    config = ThrottlingConfiguration.ENDPOINT_THROTTLES
    
    if view_name in config:
        if action in config[view_name]:
            return config[view_name][action]
    
    return ThrottlingConfiguration.DEFAULT_THROTTLE_CLASSES


def apply_throttling_to_view(view_class, endpoint_config):
    """Apply throttling configuration to a view."""
    if hasattr(view_class, 'throttle_classes'):
        view_class.throttle_classes = endpoint_config
    
    logger.info(f"Applied throttling config to {view_class.__name__}")


class DynamicThrottleRateHandler:
    """Handle dynamic throttle rate adjustments."""
    
    @staticmethod
    def get_user_throttle_rate(user, is_premium=False, is_admin=False):
        """Get throttle rate based on user properties."""
        if is_admin:
            return '10000/hour'
        elif is_premium:
            return '5000/hour'
        else:
            return '1000/hour'
    
    @staticmethod
    def adjust_rate_for_load(current_rate, server_load_percentage):
        """Adjust throttle rate based on server load."""
        if server_load_percentage > 80:
            # Reduce rates by 50% under high load
            return f"{int(int(current_rate.split('/')[0]) * 0.5)}/{current_rate.split('/')[1]}"
        elif server_load_percentage > 60:
            # Reduce rates by 25%
            return f"{int(int(current_rate.split('/')[0]) * 0.75)}/{current_rate.split('/')[1]}"
        return current_rate


# Logging for throttle events
class ThrottleLogger:
    """Log throttle events for monitoring."""
    
    @staticmethod
    def log_throttle_hit(request, throttle_class):
        """Log when throttle limit is hit."""
        logger.warning(
            f"Throttle limit hit",
            extra={
                'user': request.user.username if request.user else 'anonymous',
                'method': request.method,
                'path': request.path,
                'throttle_class': throttle_class.__class__.__name__
            }
        )
    
    @staticmethod
    def log_throttle_check(request, throttle_class, allowed):
        """Log throttle checks."""
        if not allowed:
            ThrottleLogger.log_throttle_hit(request, throttle_class)


# Settings to add to Django settings.py:
SETTINGS_CONFIGURATION = """
# Rate Limiting Configuration
REST_FRAMEWORK = {
    ...
    'DEFAULT_THROTTLE_CLASSES': [
        'app1.api_throttling.StandardUserThrottle',
        'app1.api_throttling.StandardAnonThrottle',
    ],
    'THROTTLE_RATES': {
        'standard_user': '1000/hour',
        'premium_user': '5000/hour',
        'standard_anon': '100/hour',
        'bulk_operations': '50/hour',
        'burst': '10/minute',
        'admin': '10000/hour',
        'analytics': '500/hour',
    }
}

# Cache configuration for throttle storage
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
"""

logger.info("Rate limiting and throttling configuration loaded")
