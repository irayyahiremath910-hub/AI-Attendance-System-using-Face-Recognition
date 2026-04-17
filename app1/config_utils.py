"""
Configuration utilities and helper functions
Centralized settings management and utility functions
"""

import os
from typing import Dict, List, Any
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AppConfig:
    """Centralized application configuration"""

    # Cache settings
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True') == 'True'
    CACHE_TIMEOUT_SHORT = int(os.getenv('CACHE_TIMEOUT_SHORT', '300'))
    CACHE_TIMEOUT_MEDIUM = int(os.getenv('CACHE_TIMEOUT_MEDIUM', '1800'))
    CACHE_TIMEOUT_LONG = int(os.getenv('CACHE_TIMEOUT_LONG', '86400'))

    # Batch processing settings
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))
    MAX_BATCH_RETRIES = int(os.getenv('MAX_BATCH_RETRIES', '3'))

    # Search settings
    SEARCH_RESULTS_LIMIT = int(os.getenv('SEARCH_RESULTS_LIMIT', '1000'))
    SEARCH_TIMEOUT_SECONDS = int(os.getenv('SEARCH_TIMEOUT_SECONDS', '30'))

    # Email settings
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False') == 'True'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'attendance@system.local')

    # Security settings
    SECURITY_ENABLED = os.getenv('SECURITY_ENABLED', 'True') == 'True'
    AUDIT_LOGGING_ENABLED = os.getenv('AUDIT_LOGGING_ENABLED', 'True') == 'True'
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True') == 'True'
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))

    # API settings
    API_PAGE_SIZE = int(os.getenv('API_PAGE_SIZE', '20'))
    API_MAX_PAGE_SIZE = int(os.getenv('API_MAX_PAGE_SIZE', '100'))

    # Attendance settings
    CHECK_IN_START_TIME = os.getenv('CHECK_IN_START_TIME', '08:00')
    CHECK_IN_END_TIME = os.getenv('CHECK_IN_END_TIME', '10:00')
    LATE_THRESHOLD_MINUTES = int(os.getenv('LATE_THRESHOLD_MINUTES', '15'))

    # File upload settings
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '10'))
    ALLOWED_IMAGE_FORMATS = os.getenv(
        'ALLOWED_IMAGE_FORMATS',
        'jpg,jpeg,png,gif'
    ).split(',')

    # Face recognition settings
    FACE_RECOGNITION_CONFIDENCE = float(os.getenv('FACE_RECOGNITION_CONFIDENCE', '0.6'))
    FACE_RECOGNITION_MODEL = os.getenv('FACE_RECOGNITION_MODEL', 'hog')

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            'cache': {
                'enabled': cls.CACHE_ENABLED,
                'timeout_short': cls.CACHE_TIMEOUT_SHORT,
                'timeout_medium': cls.CACHE_TIMEOUT_MEDIUM,
                'timeout_long': cls.CACHE_TIMEOUT_LONG,
            },
            'batch_processing': {
                'batch_size': cls.BATCH_SIZE,
                'max_retries': cls.MAX_BATCH_RETRIES,
            },
            'search': {
                'results_limit': cls.SEARCH_RESULTS_LIMIT,
                'timeout_seconds': cls.SEARCH_TIMEOUT_SECONDS,
            },
            'security': {
                'enabled': cls.SECURITY_ENABLED,
                'audit_logging': cls.AUDIT_LOGGING_ENABLED,
                'rate_limit': {
                    'enabled': cls.RATE_LIMIT_ENABLED,
                    'requests': cls.RATE_LIMIT_REQUESTS,
                    'window': cls.RATE_LIMIT_WINDOW,
                }
            }
        }

    @classmethod
    def is_valid(cls) -> bool:
        """Validate configuration"""
        try:
            # Validate numeric values
            assert cls.BATCH_SIZE > 0, "BATCH_SIZE must be positive"
            assert cls.LATE_THRESHOLD_MINUTES >= 0, "LATE_THRESHOLD_MINUTES must be non-negative"
            assert 0 <= cls.FACE_RECOGNITION_CONFIDENCE <= 1, "FACE_RECOGNITION_CONFIDENCE must be between 0 and 1"

            return True
        except AssertionError as e:
            logger.error(f"Configuration validation error: {str(e)}")
            return False


class Constants:
    """Application constants"""

    # Status constants
    STATUS_PRESENT = 'Present'
    STATUS_ABSENT = 'Absent'
    STATUS_LATE = 'Late'
    STATUS_LEAVE = 'Leave'
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_LEAVE, 'Leave'),
    ]

    # Attendance modes
    MODE_MANUAL = 'manual'
    MODE_CAMERA = 'camera'
    MODE_SELFIE = 'selfie'
    MODE_CHOICES = [
        (MODE_MANUAL, 'Manual'),
        (MODE_CAMERA, 'Camera'),
        (MODE_SELFIE, 'Selfie'),
    ]

    # User roles
    ROLE_ADMIN = 'admin'
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STUDENT, 'Student'),
    ]

    # Time constants
    SCHOOL_YEAR_START_MONTH = 1
    SCHOOL_YEAR_END_MONTH = 12
    WORKING_DAYS_PER_WEEK = 5

    # Notification types
    NOTIFICATION_EMAIL = 'email'
    NOTIFICATION_SMS = 'sms'
    NOTIFICATION_PUSH = 'push'
    NOTIFICATION_TYPES = [
        (NOTIFICATION_EMAIL, 'Email'),
        (NOTIFICATION_SMS, 'SMS'),
        (NOTIFICATION_PUSH, 'Push'),
    ]


class DateTimeHelper:
    """Helper functions for date and time operations"""

    @staticmethod
    def get_current_date():
        """Get current date"""
        from datetime import date
        return date.today()

    @staticmethod
    def get_current_time():
        """Get current time"""
        from datetime import datetime
        return datetime.now().time()

    @staticmethod
    def get_current_datetime():
        """Get current datetime"""
        from datetime import datetime
        return datetime.now()

    @staticmethod
    def is_check_in_time(time_obj) -> bool:
        """Check if time is within check-in window"""
        from datetime import datetime, time as datetime_time

        start_time = datetime.strptime(
            AppConfig.CHECK_IN_START_TIME,
            '%H:%M'
        ).time()
        end_time = datetime.strptime(
            AppConfig.CHECK_IN_END_TIME,
            '%H:%M'
        ).time()

        return start_time <= time_obj <= end_time

    @staticmethod
    def is_late(time_obj) -> bool:
        """Check if time is late"""
        from datetime import datetime, timedelta, time as datetime_time

        start_time = datetime.strptime(
            AppConfig.CHECK_IN_START_TIME,
            '%H:%M'
        ).time()
        late_threshold = datetime.combine(
            datetime.today(),
            start_time
        ) + timedelta(minutes=AppConfig.LATE_THRESHOLD_MINUTES)

        check_time = datetime.combine(datetime.today(), time_obj)

        return check_time > late_threshold

    @staticmethod
    def get_date_range(days: int = 7):
        """Get date range for last N days"""
        from datetime import date, timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        return start_date, end_date

    @staticmethod
    def get_week_dates():
        """Get dates for current week"""
        from datetime import date, timedelta

        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        return monday, sunday

    @staticmethod
    def get_month_dates():
        """Get dates for current month"""
        from datetime import date
        from calendar import monthrange

        today = date.today()
        year = today.year
        month = today.month

        first_day = date(year, month, 1)
        last_day_num = monthrange(year, month)[1]
        last_day = date(year, month, last_day_num)

        return first_day, last_day


class StringHelper:
    """Helper functions for string operations"""

    @staticmethod
    def truncate(text: str, length: int = 100, suffix: str = '...') -> str:
        """Truncate text to specified length"""
        if len(text) <= length:
            return text
        return text[:length - len(suffix)] + suffix

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove special characters from filename"""
        import re
        return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to slug format"""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        return text.strip('-')

    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone number"""
        phone = ''.join(c for c in phone if c.isdigit())
        if len(phone) == 10:
            return f"+91-{phone[:5]}-{phone[5:]}"
        return phone

    @staticmethod
    def extract_initials(name: str) -> str:
        """Extract initials from name"""
        return ''.join(word[0].upper() for word in name.split() if word)


class ValidationHelper:
    """Helper functions for validation"""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number"""
        import re
        phone = ''.join(c for c in phone if c.isdigit())
        return len(phone) in [10, 11, 12]

    @staticmethod
    def is_valid_roll_number(roll: str) -> bool:
        """Validate roll number format"""
        import re
        return bool(re.match(r'^[A-Z]{1,3}\d{3,4}$', roll))

    @staticmethod
    def validate_image_file(file) -> bool:
        """Validate image file"""
        if not file:
            return False

        # Check file size
        max_size = AppConfig.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file.size > max_size:
            return False

        # Check file extension
        ext = file.name.split('.')[-1].lower()
        if ext not in AppConfig.ALLOWED_IMAGE_FORMATS:
            return False

        return True


class ReportGenerator:
    """Generate various reports"""

    @staticmethod
    def generate_attendance_report(student_id: int, format: str = 'json'):
        """Generate attendance report for student"""
        from app1.models import Student, Attendance

        try:
            student = Student.objects.get(id=student_id)
            records = Attendance.objects.filter(student=student)

            report = {
                'student': {
                    'id': student.id,
                    'name': student.name,
                    'roll_number': student.roll_number,
                },
                'generated_at': datetime.now().isoformat(),
                'statistics': {
                    'total': records.count(),
                    'present': records.filter(status='Present').count(),
                    'absent': records.filter(status='Absent').count(),
                    'late': records.filter(status='Late').count(),
                }
            }

            if format == 'json':
                return json.dumps(report, indent=2)
            elif format == 'dict':
                return report

        except Student.DoesNotExist:
            return None

    @staticmethod
    def generate_class_report(class_name: str, start_date=None, end_date=None):
        """Generate report for entire class"""
        from app1.models import Student, Attendance
        from datetime import date

        if not start_date:
            start_date = date.today() - __import__('datetime').timedelta(days=30)
        if not end_date:
            end_date = date.today()

        students = Student.objects.filter(student_class__icontains=class_name)
        records = Attendance.objects.filter(
            student__in=students,
            date__range=[start_date, end_date]
        )

        report = {
            'class': class_name,
            'period': f"{start_date} to {end_date}",
            'total_students': students.count(),
            'total_records': records.count(),
            'statistics': {
                'present': records.filter(status='Present').count(),
                'absent': records.filter(status='Absent').count(),
                'late': records.filter(status='Late').count(),
            }
        }

        return report
