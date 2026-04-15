"""
Enhanced error handling and security middleware
Provides comprehensive request/response logging, error handling, and security features
"""

import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware for comprehensive request/response logging"""

    def process_request(self, request):
        """Log incoming requests"""
        request._request_start_time = time.time()
        
        # Log request details
        logger.info(
            f"Incoming {request.method} request to {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'remote_addr': self.get_client_ip(request),
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous'
            }
        )
        
        return None

    def process_response(self, request, response):
        """Log outgoing responses"""
        if hasattr(request, '_request_start_time'):
            elapsed_time = time.time() - request._request_start_time
            
            logger.info(
                f"Response {response.status_code} in {elapsed_time:.3f}s for {request.method} {request.path}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'elapsed_time': elapsed_time,
                    'remote_addr': self.get_client_ip(request)
                }
            )
        
        return response

    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'Unknown')


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware for comprehensive error handling"""

    def process_exception(self, request, exception):
        """Handle exceptions and return proper JSON responses"""
        logger.error(
            f"Exception in {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={'user': str(request.user) if request.user.is_authenticated else 'Anonymous'}
        )

        # Return appropriate error response
        if isinstance(exception, PermissionError):
            return JsonResponse(
                {'error': 'Permission denied', 'detail': str(exception)},
                status=status.HTTP_403_FORBIDDEN
            )
        elif isinstance(exception, ValueError):
            return JsonResponse(
                {'error': 'Invalid value', 'detail': str(exception)},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return JsonResponse(
                {'error': 'Internal server error', 'detail': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses"""

    def process_response(self, request, response):
        """Add security headers"""
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Strict transport security
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content security policy
        response['Content-Security-Policy'] = "default-src 'self'"
        
        return response


class RateLimitingMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.request_counts = {}

    def process_request(self, request):
        """Check rate limits"""
        client_ip = self.get_client_ip(request)
        
        # Reset counts if needed (simple implementation)
        current_time = time.time()
        self.request_counts[client_ip] = [
            ts for ts in self.request_counts.get(client_ip, [])
            if current_time - ts < 60  # Keep only requests from last 60 seconds
        ]
        
        # Track this request
        self.request_counts[client_ip] = self.request_counts.get(client_ip, []) + [current_time]
        
        # Check rate limit (max 100 requests per minute)
        if len(self.request_counts[client_ip]) > 100:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JsonResponse(
                {'error': 'Rate limit exceeded', 'detail': 'Too many requests. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        return None

    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'Unknown')


class ValidationMiddleware(MiddlewareMixin):
    """Validate request data and structure"""

    def process_request(self, request):
        """Validate incoming requests"""
        # Validate content type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            
            if not content_type and request.body:
                logger.warning(f"No content type for {request.method} request to {request.path}")

        return None


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Monitor and log performance metrics"""
    
    SLOW_REQUEST_THRESHOLD = 1.0  # 1 second

    def process_request(self, request):
        """Start performance tracking"""
        request._performance_start = time.time()
        return None

    def process_response(self, request, response):
        """Log performance metrics for slow requests"""
        if hasattr(request, '_performance_start'):
            elapsed_time = time.time() - request._performance_start
            
            if elapsed_time > self.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} took {elapsed_time:.3f}s",
                    extra={
                        'method': request.method,
                        'path': request.path,
                        'elapsed_time': elapsed_time,
                        'status_code': response.status_code
                    }
                )
        
        return response


class AuditLoggingMiddleware(MiddlewareMixin):
    """Audit logging for sensitive operations"""

    SENSITIVE_PATHS = [
        '/api/students/bulk_authorize/',
        '/api/students/send_bulk_reminders/',
        '/admin/',
    ]

    def process_request(self, request):
        """Log sensitive operations"""
        for path in self.SENSITIVE_PATHS:
            if path in request.path:
                logger.info(
                    f"Audit: {request.method} {request.path} by {request.user}",
                    extra={
                        'audit': True,
                        'user': str(request.user),
                        'method': request.method,
                        'path': request.path,
                        'ip': self.get_client_ip(request)
                    }
                )
        
        return None

    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'Unknown')
