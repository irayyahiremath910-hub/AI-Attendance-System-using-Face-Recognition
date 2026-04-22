"""Unit Tests for API Filters, Pagination, and Validators - Day 8

This module contains comprehensive unit tests for the advanced API features
added in Day 7, ensuring data integrity and proper functionality.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from app1.models import Student, Attendance
from app1.api_filters import StudentFilter, AttendanceFilter
from app1.api_pagination import StandardPagination, StudentCursorPagination
from app1.api_validators import (
    StudentDataValidator, AttendanceDataValidator, 
    BulkOperationValidator, QueryParamValidator
)
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class StudentFilterTestCase(TestCase):
    """Test suite for StudentFilter."""
    
    def setUp(self):
        """Create test students."""
        self.student1 = Student.objects.create(
            name='John Doe',
            email='john@example.com',
            student_class='A',
            authorized=True
        )
        self.student2 = Student.objects.create(
            name='Jane Smith',
            email='jane@example.com',
            student_class='B',
            authorized=False
        )
        self.factory = APIRequestFactory()
    
    def test_filter_by_name(self):
        """Test filtering students by name."""
        request = self.factory.get('/api/students/?name=John')
        filter_obj = StudentFilter(request.GET, queryset=Student.objects.all())
        assert filter_obj.qs.count() == 1
        assert filter_obj.qs.first().name == 'John Doe'
    
    def test_filter_by_authorized_status(self):
        """Test filtering by authorization status."""
        request = self.factory.get('/api/students/?authorized=true')
        filter_obj = StudentFilter(request.GET, queryset=Student.objects.all())
        assert filter_obj.qs.count() == 1
        assert filter_obj.qs.first().authorized is True
    
    def test_filter_by_class(self):
        """Test filtering by student class."""
        request = self.factory.get('/api/students/?student_class=A')
        filter_obj = StudentFilter(request.GET, queryset=Student.objects.all())
        assert filter_obj.qs.count() == 1
        assert filter_obj.qs.first().student_class == 'A'
    
    def test_filter_by_email(self):
        """Test filtering by email."""
        request = self.factory.get('/api/students/?email=jane')
        filter_obj = StudentFilter(request.GET, queryset=Student.objects.all())
        assert filter_obj.qs.count() == 1
        assert filter_obj.qs.first().email == 'jane@example.com'
    
    def test_multi_field_search(self):
        """Test multi-field search functionality."""
        request = self.factory.get('/api/students/?search=Jane')
        filter_obj = StudentFilter(request.GET, queryset=Student.objects.all())
        results = filter_obj.qs
        assert results.count() >= 1
        assert any(s.name == 'Jane Smith' for s in results)


class AttendanceFilterTestCase(TestCase):
    """Test suite for AttendanceFilter."""
    
    def setUp(self):
        """Create test data."""
        self.student = Student.objects.create(
            name='Test Student',
            email='test@example.com',
            student_class='A'
        )
        now = timezone.now()
        self.attendance1 = Attendance.objects.create(
            student=self.student,
            date=now.date(),
            check_in_time=now,
            check_out_time=None
        )
        self.attendance2 = Attendance.objects.create(
            student=self.student,
            date=(now - timedelta(days=1)).date(),
            check_in_time=now - timedelta(days=1),
            check_out_time=now - timedelta(days=1, hours=1)
        )
        self.factory = APIRequestFactory()
    
    def test_filter_by_student_name(self):
        """Test filtering by student name."""
        request = self.factory.get('/api/attendance/?student_name=Test')
        filter_obj = AttendanceFilter(request.GET, queryset=Attendance.objects.all())
        assert filter_obj.qs.count() >= 1
    
    def test_filter_by_date_range(self):
        """Test filtering by date range."""
        today = timezone.now().date()
        request = self.factory.get(f'/api/attendance/?date_from={today}&date_to={today}')
        filter_obj = AttendanceFilter(request.GET, queryset=Attendance.objects.all())
        assert filter_obj.qs.count() >= 1
    
    def test_filter_by_has_check_in(self):
        """Test filtering by check-in presence."""
        request = self.factory.get('/api/attendance/?has_check_in=true')
        filter_obj = AttendanceFilter(request.GET, queryset=Attendance.objects.all())
        assert all(a.check_in_time is not None for a in filter_obj.qs)
    
    def test_filter_by_has_check_out(self):
        """Test filtering by check-out presence."""
        request = self.factory.get('/api/attendance/?has_check_out=true')
        filter_obj = AttendanceFilter(request.GET, queryset=Attendance.objects.all())
        assert all(a.check_out_time is not None for a in filter_obj.qs)


class StudentDataValidatorTestCase(TestCase):
    """Test suite for StudentDataValidator."""
    
    def test_valid_name(self):
        """Test validation of valid names."""
        valid_names = ['John Doe', 'Jane Smith', 'Ali Hassan']
        for name in valid_names:
            result = StudentDataValidator.validate_name(name)
            assert result == name.strip()
    
    def test_invalid_name_too_short(self):
        """Test validation rejects names that are too short."""
        with pytest.raises(ValidationError):
            StudentDataValidator.validate_name('J')
    
    def test_invalid_name_with_numbers(self):
        """Test validation rejects names with numbers."""
        with pytest.raises(ValidationError):
            StudentDataValidator.validate_name('John123')
    
    def test_valid_email(self):
        """Test validation of valid emails."""
        valid_emails = ['john@example.com', 'jane.smith@university.ac.uk']
        for email in valid_emails:
            result = StudentDataValidator.validate_email(email)
            assert result == email.lower().strip()
    
    def test_invalid_email_format(self):
        """Test validation rejects invalid email formats."""
        invalid_emails = ['invalid', 'notanemail@', '@example.com']
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                StudentDataValidator.validate_email(email)
    
    def test_valid_phone_number(self):
        """Test validation of valid phone numbers."""
        valid_phones = ['+1-234-567-8900', '9876543210', '+44 20 7946 0958']
        for phone in valid_phones:
            result = StudentDataValidator.validate_phone_number(phone)
            assert result is not None
    
    def test_invalid_phone_number(self):
        """Test validation rejects invalid phone numbers."""
        with pytest.raises(ValidationError):
            StudentDataValidator.validate_phone_number('abc-def-ghij')


class AttendanceDataValidatorTestCase(TestCase):
    """Test suite for AttendanceDataValidator."""
    
    def test_valid_date_string(self):
        """Test validation of valid date strings."""
        today = timezone.now().date()
        result = AttendanceDataValidator.validate_date(str(today))
        assert result == today
    
    def test_future_date_rejected(self):
        """Test that future dates are rejected."""
        future_date = (timezone.now() + timedelta(days=1)).date()
        with pytest.raises(ValidationError):
            AttendanceDataValidator.validate_date(str(future_date))
    
    def test_valid_check_times(self):
        """Test validation of valid check-in/out times."""
        now = timezone.now()
        check_in = now
        check_out = now + timedelta(hours=1)
        result = AttendanceDataValidator.validate_check_in_time(check_in, check_out)
        assert result == check_in
    
    def test_invalid_check_times_ordering(self):
        """Test validation rejects out-of-order times."""
        now = timezone.now()
        check_in = now + timedelta(hours=1)
        check_out = now
        with pytest.raises(ValidationError):
            AttendanceDataValidator.validate_check_in_time(check_in, check_out)


class BulkOperationValidatorTestCase(TestCase):
    """Test suite for BulkOperationValidator."""
    
    def test_valid_bulk_ids(self):
        """Test validation of valid bulk ID lists."""
        valid_ids = [1, 2, 3, 4, 5]
        result = BulkOperationValidator.validate_bulk_ids(valid_ids)
        assert result == valid_ids
    
    def test_invalid_bulk_too_many_ids(self):
        """Test validation rejects too many IDs."""
        too_many_ids = list(range(1, 150))
        with pytest.raises(ValidationError):
            BulkOperationValidator.validate_bulk_ids(too_many_ids)
    
    def test_invalid_bulk_empty_list(self):
        """Test validation rejects empty list."""
        with pytest.raises(ValidationError):
            BulkOperationValidator.validate_bulk_ids([])
    
    def test_invalid_bulk_non_integer(self):
        """Test validation rejects non-integer IDs."""
        with pytest.raises(ValidationError):
            BulkOperationValidator.validate_bulk_ids([1, 2, 'three'])


class QueryParamValidatorTestCase(TestCase):
    """Test suite for QueryParamValidator."""
    
    def test_valid_page_size(self):
        """Test validation of valid page sizes."""
        valid_sizes = ['10', '50', '100']
        for size in valid_sizes:
            result = QueryParamValidator.validate_page_size(size)
            assert isinstance(result, int)
    
    def test_invalid_page_size_too_large(self):
        """Test validation rejects page sizes that are too large."""
        with pytest.raises(ValidationError):
            QueryParamValidator.validate_page_size('500')
    
    def test_invalid_page_size_zero(self):
        """Test validation rejects zero page size."""
        with pytest.raises(ValidationError):
            QueryParamValidator.validate_page_size('0')
    
    def test_valid_date_range(self):
        """Test validation of valid date ranges."""
        start = timezone.now().date()
        end = start + timedelta(days=10)
        result = QueryParamValidator.validate_date_range(start, end)
        assert result == (start, end)
    
    def test_invalid_date_range_reversed(self):
        """Test validation rejects reversed date ranges."""
        start = timezone.now().date()
        end = start - timedelta(days=10)
        with pytest.raises(ValidationError):
            QueryParamValidator.validate_date_range(start, end)


class PaginationTestCase(TestCase):
    """Test suite for pagination functionality."""
    
    def setUp(self):
        """Create test students for pagination."""
        for i in range(50):
            Student.objects.create(
                name=f'Student {i}',
                email=f'student{i}@example.com',
                student_class='A'
            )
    
    def test_standard_pagination_first_page(self):
        """Test first page of standard pagination."""
        from rest_framework.request import Request
        request = APIRequestFactory().get('/api/students/')
        drf_request = Request(request)
        
        paginator = StandardPagination()
        queryset = Student.objects.all()
        paginated = paginator.paginate_queryset(queryset, drf_request)
        
        assert len(paginated) == 20
        assert paginator.page.number == 1
    
    def test_cursor_pagination(self):
        """Test cursor pagination functionality."""
        from rest_framework.request import Request
        request = APIRequestFactory().get('/api/students/')
        drf_request = Request(request)
        
        paginator = StudentCursorPagination()
        queryset = Student.objects.all().order_by('-id')
        paginated = paginator.paginate_queryset(queryset, drf_request)
        
        assert len(paginated) == 30


# Performance tests
class PerformanceTestCase(TestCase):
    """Test performance of filters and pagination."""
    
    def setUp(self):
        """Create large dataset."""
        for i in range(100):
            Student.objects.create(
                name=f'Student {i}',
                email=f'student{i}@example.com',
                student_class='A'
            )
    
    def test_filter_performance(self):
        """Test filter performance on large dataset."""
        import time
        start = time.time()
        
        request = APIRequestFactory().get('/api/students/?authorized=true')
        filter_obj = StudentFilter(request.GET, queryset=Student.objects.all())
        list(filter_obj.qs)
        
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should complete in less than 1 second
        logger.info(f"Filter performance test completed in {elapsed:.3f}s")
    
    def test_pagination_performance(self):
        """Test pagination performance on large dataset."""
        import time
        from rest_framework.request import Request
        
        start = time.time()
        request = APIRequestFactory().get('/api/students/')
        drf_request = Request(request)
        
        paginator = StandardPagination()
        queryset = Student.objects.all()
        paginator.paginate_queryset(queryset, drf_request)
        
        elapsed = time.time() - start
        assert elapsed < 0.5  # Should complete in less than 500ms
        logger.info(f"Pagination performance test completed in {elapsed:.3f}s")
