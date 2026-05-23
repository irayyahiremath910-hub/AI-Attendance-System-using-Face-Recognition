"""
Security Utilities for AI Attendance System

Provides security-related helper functions for authentication, authorization, and security checks.
"""

import hashlib
import secrets
from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from decouple import config


def generate_secure_token(length=32):
    """
    Generate a cryptographically secure random token.
    
    Args:
        length (int): Length of the token in bytes
        
    Returns:
        str: Secure random hex token
    """
    return secrets.token_hex(length)


def hash_password_field(value):
    """
    Hash a value using SHA-256 (for additional security, not as replacement for Django's hasher).
    
    Args:
        value (str): Value to hash
        
    Returns:
        str: SHA-256 hash
    """
    return hashlib.sha256(value.encode()).hexdigest()


def verify_api_key(api_key):
    """
    Verify if API key is valid.
    
    Args:
        api_key (str): API key to verify
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_api_keys = config('VALID_API_KEYS', default='', cast=lambda x: x.split(',') if x else [])
    return api_key in valid_api_keys


def require_api_key(view_func):
    """
    Decorator to require valid API key for view.
    
    Usage:
        @require_api_key
        def my_api_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        
        if not api_key:
            return JsonResponse({'error': 'API key required'}, status=401)
        
        if not verify_api_key(api_key):
            return JsonResponse({'error': 'Invalid API key'}, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def check_ip_whitelist(request):
    """
    Check if request IP is in whitelist.
    
    Args:
        request: Django request object
        
    Returns:
        bool: True if IP is whitelisted, False otherwise
    """
    ip_whitelist = config('IP_WHITELIST', default='', cast=lambda x: x.split(',') if x else [])
    
    # If no whitelist is configured, allow all
    if not ip_whitelist:
        return True
    
    client_ip = get_client_ip(request)
    return client_ip in ip_whitelist


def get_client_ip(request):
    """
    Get client IP address from request, handling proxies.
    
    Args:
        request: Django request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def require_https(view_func):
    """
    Decorator to require HTTPS for view.
    
    Usage:
        @require_https
        def my_secure_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.is_secure() and not settings.DEBUG:
            return HttpResponseForbidden('HTTPS required')
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_staff(view_func):
    """
    Decorator to require staff/admin user.
    
    Usage:
        @require_staff
        def admin_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden('Staff access required')
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_superuser(view_func):
    """
    Decorator to require superuser.
    
    Usage:
        @require_superuser
        def superuser_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('Superuser access required')
        return view_func(request, *args, **kwargs)
    
    return wrapper


def rate_limit_check(request, limit=100, window=3600):
    """
    Simple rate limiting check (implement with cache for production).
    
    Args:
        request: Django request object
        limit (int): Request limit
        window (int): Time window in seconds
        
    Returns:
        bool: True if within limit, False if exceeded
    """
    # TODO: Implement with Django cache for production
    # This is a placeholder for demonstration
    return True


def get_security_headers():
    """
    Get recommended security headers dictionary.
    
    Returns:
        dict: Security headers to add to response
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Content-Security-Policy': settings.SECURE_CONTENT_SECURITY_POLICY,
    }


def validate_password_strength(password):
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, message)
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'
    
    if not any(c.isupper() for c in password):
        return False, 'Password must contain uppercase letter'
    
    if not any(c.islower() for c in password):
        return False, 'Password must contain lowercase letter'
    
    if not any(c.isdigit() for c in password):
        return False, 'Password must contain digit'
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, 'Password must contain special character'
    
    return True, 'Password is strong'


def sanitize_input(user_input, max_length=1000):
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        user_input (str): User input to sanitize
        max_length (int): Maximum allowed length
        
    Returns:
        str: Sanitized input
    """
    if not isinstance(user_input, str):
        return ''
    
    # Limit length
    user_input = user_input[:max_length]
    
    # Remove dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    for char in dangerous_chars:
        user_input = user_input.replace(char, '')
    
    return user_input.strip()
