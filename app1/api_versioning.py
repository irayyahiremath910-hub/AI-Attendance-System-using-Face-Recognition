"""
API versioning system for managing multiple API versions
Ensures backward compatibility while supporting new features
"""

from functools import wraps
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class APIVersion:
    """Represents an API version"""

    def __init__(self, version_number, status='active', deprecated_date=None):
        self.version_number = version_number
        self.status = status  # 'active', 'beta', 'deprecated'
        self.deprecated_date = deprecated_date
        self.features = {}
        self.breaking_changes = []
        self.enhancements = []

    def add_feature(self, feature_name, feature_func):
        """Add feature to version"""
        self.features[feature_name] = feature_func

    def mark_deprecated(self, date):
        """Mark version as deprecated"""
        self.status = 'deprecated'
        self.deprecated_date = date

    def get_info(self):
        """Get version information"""
        return {
            'version': self.version_number,
            'status': self.status,
            'deprecated_date': self.deprecated_date.isoformat() if self.deprecated_date else None,
            'features_count': len(self.features),
            'breaking_changes': self.breaking_changes,
            'enhancements': self.enhancements,
        }


class VersionManager:
    """Manages API versions"""

    def __init__(self):
        self.versions = {}
        self.current_version = None
        self._initialize_versions()

    def _initialize_versions(self):
        """Initialize default versions"""
        v1 = APIVersion('1.0', status='deprecated')
        v2 = APIVersion('2.0', status='active')
        v3 = APIVersion('3.0', status='beta')

        self.register_version(v1)
        self.register_version(v2)
        self.register_version(v3)

        self.current_version = '3.0'

    def register_version(self, api_version):
        """Register API version"""
        self.versions[api_version.version_number] = api_version
        logger.info(f"API version registered: {api_version.version_number}")

    def get_version(self, version_number):
        """Get specific version"""
        return self.versions.get(version_number)

    def get_current_version(self):
        """Get current version"""
        return self.versions.get(self.current_version)

    def set_current_version(self, version_number):
        """Set current version"""
        if version_number in self.versions:
            self.current_version = version_number
            logger.info(f"Current API version set to: {version_number}")

    def list_versions(self):
        """List all versions"""
        return [
            {
                'version': v.version_number,
                'status': v.status,
                'is_current': v.version_number == self.current_version,
            }
            for v in self.versions.values()
        ]

    def is_version_active(self, version_number):
        """Check if version is active"""
        version = self.get_version(version_number)
        return version and version.status in ['active', 'beta']

    def is_version_deprecated(self, version_number):
        """Check if version is deprecated"""
        version = self.get_version(version_number)
        return version and version.status == 'deprecated'


class APIResponseFormatter:
    """Format API responses for different versions"""

    @staticmethod
    def format_v1_response(data, status='success'):
        """V1.0 response format (legacy)"""
        return {
            'status': status,
            'data': data,
        }

    @staticmethod
    def format_v2_response(data, status='success', meta=None):
        """V2.0 response format"""
        return {
            'status': status,
            'data': data,
            'meta': meta or {},
            'timestamp': __import__('datetime').datetime.now().isoformat(),
        }

    @staticmethod
    def format_v3_response(data, status='success', meta=None, warnings=None):
        """V3.0 response format (current)"""
        return {
            'status': status,
            'data': data,
            'meta': meta or {},
            'warnings': warnings or [],
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'api_version': '3.0',
        }

    @staticmethod
    def format_error_response(version, error_code, message, details=None):
        """Format error response for version"""
        if version == '1.0':
            return {
                'status': 'error',
                'error_code': error_code,
                'message': message,
            }
        elif version == '2.0':
            return {
                'status': 'error',
                'error': {
                    'code': error_code,
                    'message': message,
                },
                'timestamp': __import__('datetime').datetime.now().isoformat(),
            }
        else:  # 3.0+
            return {
                'status': 'error',
                'error': {
                    'code': error_code,
                    'message': message,
                    'details': details,
                },
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'api_version': version,
            }


class VersionDecorator:
    """Decorators for API versioning"""

    @staticmethod
    def api_version(required_version=None, deprecated_version=None):
        """Decorator to enforce API version"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                # Get version from request
                version = request.META.get('HTTP_X_API_VERSION', '3.0')
                
                # Check version manager
                manager = VersionManager()

                # Check if version is supported
                if not manager.is_version_active(version):
                    return JsonResponse(
                        APIResponseFormatter.format_error_response(
                            version,
                            'UNSUPPORTED_VERSION',
                            f'API version {version} is not supported',
                            {'supported_versions': [v.version_number for v in manager.versions.values()]}
                        ),
                        status=400
                    )

                # Add version info to request
                request.api_version = version
                request.version_manager = manager

                # Call view
                response = view_func(request, *args, **kwargs)

                # Format response for version
                if isinstance(response, dict):
                    formatter = APIResponseFormatter()
                    if version == '1.0':
                        response = formatter.format_v1_response(response)
                    elif version == '2.0':
                        response = formatter.format_v2_response(response)
                    else:
                        response = formatter.format_v3_response(response)

                    return JsonResponse(response)

                return response

            return wrapper

        return decorator

    @staticmethod
    def deprecated_endpoint(removal_version=None, alternative=None):
        """Decorator to mark endpoint as deprecated"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                version = request.META.get('HTTP_X_API_VERSION', '3.0')

                # Add deprecation warning to response
                response = view_func(request, *args, **kwargs)

                if isinstance(response, dict):
                    warnings = response.get('warnings', [])
                    warnings.append({
                        'type': 'DEPRECATED_ENDPOINT',
                        'message': f'This endpoint is deprecated',
                        'removal_version': removal_version,
                        'alternative': alternative,
                    })
                    response['warnings'] = warnings

                return JsonResponse(response) if isinstance(response, dict) else response

            return wrapper

        return decorator


class BackwardCompatibility:
    """Handle backward compatibility between versions"""

    COMPATIBILITY_MAP = {
        '1.0': {
            'student_fields': ['id', 'name', 'email'],
            'attendance_fields': ['id', 'date', 'status'],
        },
        '2.0': {
            'student_fields': ['id', 'name', 'email', 'roll_number', 'class'],
            'attendance_fields': ['id', 'date', 'status', 'check_in_time', 'check_out_time'],
        },
        '3.0': {
            'student_fields': ['id', 'name', 'email', 'roll_number', 'class', 'authorized', 'enrollment_date'],
            'attendance_fields': ['id', 'student', 'date', 'status', 'check_in_time', 'check_out_time', 'duration'],
        }
    }

    @classmethod
    def filter_response_fields(cls, data, version, data_type='student'):
        """Filter response fields based on API version"""
        fields = cls.COMPATIBILITY_MAP.get(version, {}).get(f'{data_type}_fields', [])

        if isinstance(data, list):
            return [
                {k: v for k, v in item.items() if k in fields}
                for item in data
            ]
        elif isinstance(data, dict):
            return {k: v for k, v in data.items() if k in fields}

        return data

    @classmethod
    def transform_request(cls, data, version):
        """Transform request data for version compatibility"""
        if version == '1.0':
            # Map new fields to old names
            if 'roll_number' in data:
                data['roll'] = data.pop('roll_number')

        return data

    @classmethod
    def transform_response(cls, data, from_version, to_version):
        """Transform response from one version to another"""
        # This handles requests that need to bridge versions
        logger.info(f"Transforming response from v{from_version} to v{to_version}")
        return data


class VersioningMiddleware:
    """Middleware for API versioning"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.version_manager = VersionManager()

    def __call__(self, request):
        # Extract version from header or query param
        version = request.META.get('HTTP_X_API_VERSION') or request.GET.get('api_version', '3.0')

        # Validate version
        if not self.version_manager.is_version_active(version):
            logger.warning(f"Request to unsupported API version: {version}")

        # Attach to request
        request.api_version = version

        response = self.get_response(request)
        
        # Add version header to response
        response['X-API-Version'] = version

        return response


# Global version manager
global_version_manager = VersionManager()
