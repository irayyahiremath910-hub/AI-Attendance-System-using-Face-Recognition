"""API Request and Response Validators

This module provides validation utilities for API requests and responses
to ensure data integrity and consistency.
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class StudentDataValidator:
    """Validator for student data."""
    
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    
    @staticmethod
    def validate_name(name):
        """Validate student name."""
        if not isinstance(name, str):
            raise serializers.ValidationError("Name must be a string.")
        
        if not (StudentDataValidator.MIN_NAME_LENGTH <= len(name) <= StudentDataValidator.MAX_NAME_LENGTH):
            raise serializers.ValidationError(
                f"Name length must be between {StudentDataValidator.MIN_NAME_LENGTH} "
                f"and {StudentDataValidator.MAX_NAME_LENGTH} characters."
            )
        
        if not name.replace(' ', '').isalpha():
            raise serializers.ValidationError("Name must contain only alphabetic characters and spaces.")
        
        return name.strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        if not isinstance(email, str):
            raise serializers.ValidationError("Email must be a string.")
        
        if '@' not in email or '.' not in email:
            raise serializers.ValidationError("Invalid email format.")
        
        if len(email) > 254:
            raise serializers.ValidationError("Email is too long.")
        
        return email.lower().strip()
    
    @staticmethod
    def validate_phone_number(phone_number):
        """Validate phone number."""
        if phone_number and not phone_number.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Phone number must contain only digits, +, -, and spaces.")
        
        return phone_number.strip() if phone_number else None
    
    @staticmethod
    def validate_student_class(student_class):
        """Validate student class."""
        if not isinstance(student_class, str):
            raise serializers.ValidationError("Class must be a string.")
        
        if len(student_class.strip()) == 0:
            raise serializers.ValidationError("Class cannot be empty.")
        
        return student_class.strip()


class AttendanceDataValidator:
    """Validator for attendance data."""
    
    @staticmethod
    def validate_date(attendance_date):
        """Validate attendance date."""
        if isinstance(attendance_date, str):
            try:
                attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            except ValueError:
                raise serializers.ValidationError("Date must be in YYYY-MM-DD format.")
        
        if not isinstance(attendance_date, date):
            raise serializers.ValidationError("Invalid date format.")
        
        if attendance_date > date.today():
            raise serializers.ValidationError("Attendance date cannot be in the future.")
        
        return attendance_date
    
    @staticmethod
    def validate_check_in_time(check_in_time, check_out_time=None):
        """Validate check-in time."""
        if check_in_time and check_out_time:
            if check_in_time >= check_out_time:
                raise serializers.ValidationError("Check-in time must be before check-out time.")
        
        return check_in_time
    
    @staticmethod
    def validate_check_out_time(check_out_time, check_in_time=None):
        """Validate check-out time."""
        if check_in_time and check_out_time:
            if check_out_time <= check_in_time:
                raise serializers.ValidationError("Check-out time must be after check-in time.")
        
        return check_out_time
    
    @staticmethod
    def validate_duration(duration):
        """Validate attendance duration."""
        if duration and duration <= 0:
            raise serializers.ValidationError("Duration must be positive.")
        
        if duration and duration > 86400:  # 24 hours in seconds
            raise serializers.ValidationError("Duration cannot exceed 24 hours.")
        
        return duration


class BulkOperationValidator:
    """Validator for bulk operations."""
    
    MAX_BULK_SIZE = 100
    MIN_BULK_SIZE = 1
    
    @staticmethod
    def validate_bulk_ids(ids):
        """Validate list of IDs for bulk operations."""
        if not isinstance(ids, list):
            raise serializers.ValidationError("IDs must be a list.")
        
        if not (BulkOperationValidator.MIN_BULK_SIZE <= len(ids) <= BulkOperationValidator.MAX_BULK_SIZE):
            raise serializers.ValidationError(
                f"Number of IDs must be between {BulkOperationValidator.MIN_BULK_SIZE} "
                f"and {BulkOperationValidator.MAX_BULK_SIZE}."
            )
        
        # Check all are integers
        if not all(isinstance(id, int) for id in ids):
            raise serializers.ValidationError("All IDs must be integers.")
        
        return ids
    
    @staticmethod
    def validate_bulk_data(data):
        """Validate bulk operation data."""
        if not isinstance(data, (list, dict)):
            raise serializers.ValidationError("Data must be a list or dictionary.")
        
        if isinstance(data, list):
            if len(data) > BulkOperationValidator.MAX_BULK_SIZE:
                raise serializers.ValidationError(
                    f"Cannot process more than {BulkOperationValidator.MAX_BULK_SIZE} items."
                )
        
        return data


class QueryParamValidator:
    """Validator for query parameters."""
    
    @staticmethod
    def validate_page_size(page_size):
        """Validate page size parameter."""
        try:
            page_size = int(page_size)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Page size must be an integer.")
        
        if not (1 <= page_size <= 200):
            raise serializers.ValidationError("Page size must be between 1 and 200.")
        
        return page_size
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate date range for filtering."""
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError("Start date must be before end date.")
        
        return start_date, end_date
