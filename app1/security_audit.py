"""
Security and audit logging for the attendance system
Tracks all user actions, data modifications, and access patterns
"""

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import json
import hashlib
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    """Model for tracking all significant system actions"""

    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('AUTHORIZE', 'Authorize'),
        ('SEARCH', 'Search'),
        ('BULK_OPERATION', 'Bulk Operation'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('SUCCESS', 'Success'), ('FAILED', 'Failed'), ('ATTEMPTED', 'Attempted')],
        default='SUCCESS'
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.action} - {self.model_name} by {self.user} at {self.timestamp}"


class SecurityEventLog(models.Model):
    """Log security-related events and anomalies"""

    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    event_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.severity} at {self.timestamp}"


class AccessLog(models.Model):
    """Track access to sensitive resources"""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    resource = models.CharField(max_length=255)
    action = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    reason_failed = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['resource', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.action} - {self.resource} by {self.user}"


class AuditService:
    """Service for handling audit logging"""

    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def get_user_agent(request):
        """Extract user agent from request"""
        return request.META.get('HTTP_USER_AGENT', '')[:255]

    @staticmethod
    def log_action(
        user,
        action,
        model_name,
        object_id=None,
        object_repr='',
        changes=None,
        ip_address=None,
        user_agent='',
        status='SUCCESS',
        request=None
    ):
        """Log user action"""
        if request:
            ip_address = AuditService.get_client_ip(request)
            user_agent = AuditService.get_user_agent(request)

        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=object_id,
                object_repr=object_repr,
                changes=changes or {},
                ip_address=ip_address,
                user_agent=user_agent,
                status=status
            )
        except Exception as e:
            logger.error(f"Error logging action: {str(e)}")

    @staticmethod
    def log_security_event(
        event_type,
        severity,
        description,
        ip_address,
        user=None
    ):
        """Log security event"""
        try:
            SecurityEventLog.objects.create(
                event_type=event_type,
                severity=severity,
                user=user,
                description=description,
                ip_address=ip_address
            )

            if severity in ['HIGH', 'CRITICAL']:
                logger.warning(
                    f"Security Event: {event_type} - {severity} - {description}"
                )
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")

    @staticmethod
    def log_access(
        user,
        resource,
        action,
        ip_address,
        success=True,
        reason_failed=''
    ):
        """Log resource access"""
        try:
            AccessLog.objects.create(
                user=user,
                resource=resource,
                action=action,
                ip_address=ip_address,
                success=success,
                reason_failed=reason_failed
            )
        except Exception as e:
            logger.error(f"Error logging access: {str(e)}")


class SecurityDecorators:
    """Decorators for security enforcement"""

    @staticmethod
    def audit_action(action_type, model_name):
        """Decorator to automatically log actions"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                result = view_func(request, *args, **kwargs)

                if result.status_code in [200, 201, 204]:
                    status = 'SUCCESS'
                else:
                    status = 'FAILED'

                AuditService.log_action(
                    user=request.user if request.user.is_authenticated else None,
                    action=action_type,
                    model_name=model_name,
                    status=status,
                    request=request
                )

                return result

            return wrapper

        return decorator

    @staticmethod
    def require_permission(permission):
        """Decorator to enforce permission checks"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                ip = AuditService.get_client_ip(request)

                if not request.user.is_authenticated:
                    AuditService.log_security_event(
                        event_type='UNAUTHORIZED_ACCESS_ATTEMPT',
                        severity='MEDIUM',
                        description=f"Unauthorized access to {view_func.__name__}",
                        ip_address=ip
                    )
                    return Response(
                        {'error': 'Authentication required'},
                        status=403
                    )

                if permission and not request.user.has_perm(permission):
                    AuditService.log_security_event(
                        event_type='PERMISSION_DENIED',
                        severity='LOW',
                        description=f"Permission denied for {permission}",
                        ip_address=ip,
                        user=request.user
                    )
                    return Response(
                        {'error': 'Permission denied'},
                        status=403
                    )

                return view_func(request, *args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def rate_limit(max_requests=100, window_seconds=3600):
        """Decorator for rate limiting"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                from django.core.cache import cache

                ip = AuditService.get_client_ip(request)
                cache_key = f"rate_limit:{ip}:{view_func.__name__}"

                request_count = cache.get(cache_key, 0)

                if request_count >= max_requests:
                    AuditService.log_security_event(
                        event_type='RATE_LIMIT_EXCEEDED',
                        severity='MEDIUM',
                        description=f"Rate limit exceeded for {view_func.__name__}",
                        ip_address=ip,
                        user=request.user if request.user.is_authenticated else None
                    )
                    return Response(
                        {'error': 'Rate limit exceeded'},
                        status=429
                    )

                cache.set(cache_key, request_count + 1, window_seconds)

                return view_func(request, *args, **kwargs)

            return wrapper

        return decorator


class DataEncryption:
    """Handle sensitive data encryption"""

    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for comparison without storing plaintext"""
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email for display"""
        name, domain = email.split('@')
        masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
        return f"{masked_name}@{domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number for display"""
        if len(phone) >= 4:
            return '*' * (len(phone) - 4) + phone[-4:]
        return phone

    @staticmethod
    def should_log_data(data_type: str) -> bool:
        """Determine if data should be logged"""
        sensitive_types = ['password', 'token', 'api_key', 'credit_card']
        return data_type.lower() not in sensitive_types


class ComplianceChecker:
    """Check compliance with data protection regulations"""

    @staticmethod
    def get_user_data(user) -> dict:
        """Get all data associated with a user (GDPR compliance)"""
        from django.contrib.auth.models import User

        if isinstance(user, int):
            user = User.objects.get(id=user)

        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': DataEncryption.mask_email(user.email),
                'date_joined': user.date_joined
            },
            'actions': list(
                AuditLog.objects.filter(user=user).values(
                    'action', 'model_name', 'timestamp'
                )[:100]
            ),
            'access_logs': list(
                AccessLog.objects.filter(user=user).values(
                    'resource', 'action', 'timestamp'
                )[:100]
            )
        }

    @staticmethod
    def delete_user_data(user, keep_audit=True):
        """Delete all user data (GDPR right to deletion)"""
        try:
            audit_logs = AuditLog.objects.filter(user=user)
            access_logs = AccessLog.objects.filter(user=user)

            if not keep_audit:
                audit_logs.delete()
                access_logs.delete()
            else:
                # Keep logs but anonymize user reference
                audit_logs.update(user=None)
                access_logs.update(user=None)

            logger.info(f"Data deletion completed for user {user.id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting user data: {str(e)}")
            return False
