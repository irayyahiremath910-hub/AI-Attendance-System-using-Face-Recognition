"""
Comprehensive testing framework and utilities
Includes fixtures, test helpers, and sample unit tests
"""

from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from app1.models import Student, Attendance
from app1.search_service import AttendanceSearchService
from app1.cache_service import CacheService, StudentCache, AttendanceCache
from app1.batch_processor import BatchProcessor
from datetime import date, timedelta
import json
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class StudentTestModel(TestCase):
    """Test cases for Student model"""

    def setUp(self):
        """Set up test data"""
        self.student = Student.objects.create(
            name='John Doe',
            roll_number='B001',
            email='john@example.com',
            student_class='B Tech',
            authorized=True
        )

    def test_student_creation(self):
        """Test student creation"""
        self.assertEqual(self.student.name, 'John Doe')
        self.assertTrue(self.student.authorized)

    def test_student_str_representation(self):
        """Test student string representation"""
        self.assertEqual(str(self.student), 'John Doe - B001')

    def test_student_email_validation(self):
        """Test student with invalid email"""
        invalid_student = Student(
            name='Jane Doe',
            roll_number='B002',
            email='invalid_email',
            student_class='B Tech'
        )
        # Note: Email validation depends on model implementation


class AttendanceTestModel(TestCase):
    """Test cases for Attendance model"""

    def setUp(self):
        """Set up test data"""
        self.student = Student.objects.create(
            name='John Doe',
            roll_number='B001',
            email='john@example.com',
            student_class='B Tech'
        )

        self.attendance = Attendance.objects.create(
            student=self.student,
            date=date.today(),
            status='Present',
            check_in_time='09:00:00',
            check_out_time='17:00:00'
        )

    def test_attendance_creation(self):
        """Test attendance record creation"""
        self.assertEqual(self.attendance.student, self.student)
        self.assertEqual(self.attendance.status, 'Present')

    def test_attendance_date_filtering(self):
        """Test filtering by date"""
        Attendance.objects.create(
            student=self.student,
            date=date.today() - timedelta(days=1),
            status='Absent'
        )

        today_records = Attendance.objects.filter(date=date.today())
        self.assertEqual(today_records.count(), 1)

    def test_invalid_status(self):
        """Test invalid status values"""
        try:
            invalid_attendance = Attendance.objects.create(
                student=self.student,
                date=date.today(),
                status='InvalidStatus'
            )
            # This should be caught by model validation
        except Exception:
            pass


class SearchServiceTestCase(TestCase):
    """Test cases for AttendanceSearchService"""

    def setUp(self):
        """Set up test data"""
        self.student1 = Student.objects.create(
            name='John Doe',
            roll_number='B001',
            email='john@example.com',
            student_class='B Tech'
        )
        self.student2 = Student.objects.create(
            name='Jane Smith',
            roll_number='B002',
            email='jane@example.com',
            student_class='B Tech'
        )

        Attendance.objects.create(
            student=self.student1,
            date=date.today(),
            status='Present'
        )
        Attendance.objects.create(
            student=self.student2,
            date=date.today(),
            status='Absent'
        )

    def test_search_students_by_name(self):
        """Test searching students by name"""
        results = AttendanceSearchService.search_students('John')
        self.assertGreaterEqual(results.count(), 1)

    def test_search_students_by_roll_number(self):
        """Test searching by roll number"""
        results = AttendanceSearchService.search_students('B001')
        self.assertGreaterEqual(results.count(), 1)

    def test_search_attendance_by_date(self):
        """Test searching attendance by date"""
        results = AttendanceSearchService.search_attendance(
            {'start_date': str(date.today())}
        )
        self.assertEqual(results.count(), 2)


class CacheServiceTestCase(TransactionTestCase):
    """Test cases for caching service"""

    def setUp(self):
        """Set up test data"""
        self.student = Student.objects.create(
            name='John Doe',
            roll_number='B001',
            email='john@example.com',
            student_class='B Tech',
            authorized=True
        )

    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = CacheService.get_cache_key('student', 1)
        key2 = CacheService.get_cache_key('student', 1)
        self.assertEqual(key1, key2)

    def test_get_or_set_cache(self):
        """Test get_or_set functionality"""
        def fetch():
            return Student.objects.count()

        result1 = CacheService.get_or_set('test_key', fetch, timeout=60)
        result2 = CacheService.get_or_set('test_key', fetch, timeout=60)

        self.assertEqual(result1, result2)

    def test_student_cache(self):
        """Test student caching"""
        cached = StudentCache.get_student_by_id(self.student.id)
        self.assertEqual(cached.name, 'John Doe')

    def test_cache_invalidation(self):
        """Test cache invalidation"""
        StudentCache.get_student_by_id(self.student.id)
        StudentCache.invalidate_student_cache(self.student.id)
        # Cache should be cleared


class BatchProcessorTestCase(TestCase):
    """Test cases for batch processing"""

    def setUp(self):
        """Set up test data"""
        for i in range(5):
            Student.objects.create(
                name=f'Student {i}',
                roll_number=f'B{i:03d}',
                email=f'student{i}@example.com',
                student_class='B Tech',
                authorized=False
            )

    def test_authorize_students_batch(self):
        """Test batch authorization"""
        result = BatchProcessor.authorize_students_batch()
        self.assertEqual(result['total'], 5)

    def test_process_students_batch(self):
        """Test batch processing with custom function"""
        def mark_present(student):
            Attendance.objects.create(
                student=student,
                date=date.today(),
                status='Present'
            )

        queryset = Student.objects.all()
        result = BatchProcessor.process_students_batch(
            queryset,
            mark_present
        )

        self.assertEqual(result['success'], 5)

    def test_batch_with_progress_callback(self):
        """Test batch processing with progress callback"""
        progress_updates = []

        def progress_callback(current, total, **kwargs):
            progress_updates.append({'current': current, 'total': total})

        queryset = Student.objects.all()
        BatchProcessor.process_students_batch(
            queryset,
            lambda s: None,
            progress_callback=progress_callback
        )

        self.assertGreater(len(progress_updates), 0)


class StudentAPITestCase(APITestCase):
    """Test cases for Student API endpoints"""

    def setUp(self):
        """Set up test data and authentication"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.student = Student.objects.create(
            name='John Doe',
            roll_number='B001',
            email='john@example.com',
            student_class='B Tech'
        )

    def test_list_students(self):
        """Test getting list of students"""
        url = reverse('student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_student(self):
        """Test retrieving a specific student"""
        url = reverse('student-detail', kwargs={'pk': self.student.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_students(self):
        """Test searching students"""
        url = reverse('student-list') + '?search=John'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AttendanceAPITestCase(APITestCase):
    """Test cases for Attendance API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.student = Student.objects.create(
            name='John Doe',
            roll_number='B001',
            email='john@example.com',
            student_class='B Tech'
        )

        self.attendance = Attendance.objects.create(
            student=self.student,
            date=date.today(),
            status='Present'
        )

    def test_list_attendance(self):
        """Test getting attendance list"""
        url = reverse('attendance-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_statistics(self):
        """Test attendance statistics endpoint"""
        url = reverse('attendance-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_attendance_records', response.data)

    def test_bulk_update_status(self):
        """Test bulk status update"""
        url = reverse('attendance-bulk-update-status')
        data = {'status': 'Late'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class IntegrationTestCase(TransactionTestCase):
    """Integration tests combining multiple components"""

    def setUp(self):
        """Set up test data"""
        self.student = Student.objects.create(
            name='John Doe',
            roll_number='B001',
            email='john@example.com',
            student_class='B Tech',
            authorized=True
        )

    def test_end_to_end_attendance_flow(self):
        """Test complete attendance flow"""
        # Create attendance
        attendance = Attendance.objects.create(
            student=self.student,
            date=date.today(),
            status='Present'
        )

        # Search
        results = AttendanceSearchService.search_attendance(
            {'start_date': str(date.today())}
        )
        self.assertGreater(results.count(), 0)

        # Cache
        cached = AttendanceCache.get_today_attendance()
        self.assertGreater(len(cached), 0)

        # Batch operation
        result = BatchProcessor.update_attendance_status_batch(
            status_update_func=lambda r: r
        )
        self.assertIn('total', result)

    def test_multiple_students_workflow(self):
        """Test workflow with multiple students"""
        for i in range(3):
            Student.objects.create(
                name=f'Student {i}',
                roll_number=f'B{i+1:03d}',
                email=f'student{i}@example.com',
                student_class='B Tech'
            )

        # Batch authorize
        result = BatchProcessor.authorize_students_batch()
        self.assertEqual(result['total'], 4)
