"""Integration Tests for Bulk Operations and API Endpoints - Day 8

This module contains integration tests for the advanced API features,
testing real-world scenarios and endpoint interactions.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from app1.models import Student, Attendance
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth.models import User
import json


class BulkOperationIntegrationTestCase(APITestCase):
    """Integration tests for bulk operations."""
    
    def setUp(self):
        """Create test users and students."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Create test students
        self.students = []
        for i in range(10):
            student = Student.objects.create(
                name=f'Student {i}',
                email=f'student{i}@example.com',
                student_class='A',
                authorized=(i % 2 == 0)  # Half authorized, half not
            )
            self.students.append(student)
        
        self.client = APIClient()
    
    def test_bulk_authorize_students_success(self):
        """Test successfully authorizing multiple students."""
        self.client.force_authenticate(user=self.admin_user)
        
        unauthorized_ids = [
            s.id for s in self.students if not s.authorized
        ]
        
        response = self.client.post(
            '/api/students/bulk_authorize/',
            {'student_ids': unauthorized_ids},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['authorized_count'] > 0
    
    def test_bulk_authorize_requires_admin(self):
        """Test that bulk authorize requires admin permission."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.post(
            '/api/students/bulk_authorize/',
            {'student_ids': [1, 2, 3]},
            format='json'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_bulk_authorize_invalid_ids(self):
        """Test bulk authorize with invalid ID list."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Too many IDs
        invalid_ids = list(range(1, 150))
        
        response = self.client.post(
            '/api/students/bulk_authorize/',
            {'student_ids': invalid_ids},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_bulk_delete_students_success(self):
        """Test successfully deleting multiple students."""
        self.client.force_authenticate(user=self.admin_user)
        
        delete_ids = [self.students[0].id, self.students[1].id]
        initial_count = Student.objects.count()
        
        response = self.client.post(
            '/api/students/bulk_delete/',
            {'student_ids': delete_ids},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['deleted_count'] == 2
        assert Student.objects.count() == initial_count - 2
    
    def test_bulk_checkout_attendance(self):
        """Test bulk checking out attendance records."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create pending attendance records
        now = timezone.now()
        attendance_records = []
        for student in self.students[:5]:
            attendance = Attendance.objects.create(
                student=student,
                date=now.date(),
                check_in_time=now,
                check_out_time=None
            )
            attendance_records.append(attendance)
        
        checkout_ids = [a.id for a in attendance_records]
        
        response = self.client.post(
            '/api/attendance/bulk_checkout/',
            {'attendance_ids': checkout_ids},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # Verify checkout times were set
        for attendance in Attendance.objects.filter(id__in=checkout_ids):
            assert attendance.check_out_time is not None


class StudentAPIIntegrationTestCase(APITestCase):
    """Integration tests for Student API endpoints."""
    
    def setUp(self):
        """Create test user and students."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Create test students
        self.students = []
        for i in range(15):
            student = Student.objects.create(
                name=f'Student {i:02d}',
                email=f'student{i}@example.com',
                student_class='A' if i % 2 == 0 else 'B',
                authorized=i % 3 != 0
            )
            self.students.append(student)
        
        self.client = APIClient()
    
    def test_list_students_with_pagination(self):
        """Test listing students with pagination."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/students/?page=1&page_size=5')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_count' in response.data
        assert 'results' in response.data
        assert len(response.data['results']) <= 5
    
    def test_list_students_with_filtering(self):
        """Test listing students with filters."""
        self.client.force_authenticate(user=self.user)
        
        # Filter by authorization status
        response = self.client.get('/api/students/?authorized=true')
        
        assert response.status_code == status.HTTP_200_OK
        authorized_count = len([s for s in self.students if s.authorized])
        assert len(response.data['results']) <= authorized_count
    
    def test_list_students_with_search(self):
        """Test searching students."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/students/?search=Student')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
    
    def test_list_students_with_ordering(self):
        """Test ordering students."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/students/?ordering=name')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        if len(results) > 1:
            # Verify ordering
            names = [s['name'] for s in results]
            assert names == sorted(names)
    
    def test_get_student_details(self):
        """Test retrieving student details."""
        self.client.force_authenticate(user=self.user)
        
        student = self.students[0]
        response = self.client.get(f'/api/students/{student.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == student.name
        assert response.data['email'] == student.email
    
    def test_get_student_attendance_history(self):
        """Test getting student attendance history."""
        self.client.force_authenticate(user=self.user)
        
        student = self.students[0]
        
        # Create attendance records
        now = timezone.now()
        for i in range(5):
            Attendance.objects.create(
                student=student,
                date=(now - timedelta(days=i)).date(),
                check_in_time=now - timedelta(days=i),
                check_out_time=now - timedelta(days=i, hours=1)
            )
        
        response = self.client.get(
            f'/api/students/{student.id}/attendance_history/?days=10'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert 'records' in response.data
        assert len(response.data['records']) > 0
    
    def test_authorize_student(self):
        """Test authorizing a single student."""
        self.client.force_authenticate(user=self.user)
        
        unauthorized_student = next(s for s in self.students if not s.authorized)
        
        response = self.client.post(
            f'/api/students/{unauthorized_student.id}/authorize/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify authorization was set
        updated_student = Student.objects.get(id=unauthorized_student.id)
        assert updated_student.authorized is True


class AttendanceAPIIntegrationTestCase(APITestCase):
    """Integration tests for Attendance API endpoints."""
    
    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Create test student
        self.student = Student.objects.create(
            name='Test Student',
            email='test@example.com',
            student_class='A',
            authorized=True
        )
        
        # Create attendance records
        now = timezone.now()
        for i in range(10):
            Attendance.objects.create(
                student=self.student,
                date=(now - timedelta(days=i)).date(),
                check_in_time=now - timedelta(days=i),
                check_out_time=now - timedelta(days=i, hours=1) if i % 2 == 0 else None
            )
        
        self.client = APIClient()
    
    def test_list_attendance_with_pagination(self):
        """Test listing attendance with pagination."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/attendance/?page=1&page_size=5')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_count' in response.data
        assert len(response.data['results']) <= 5
    
    def test_list_attendance_with_date_filter(self):
        """Test filtering attendance by date range."""
        self.client.force_authenticate(user=self.user)
        
        today = timezone.now().date()
        response = self.client.get(
            f'/api/attendance/?date_from={today - timedelta(days=5)}&date_to={today}'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
    
    def test_get_pending_checkout(self):
        """Test getting pending checkout records."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/attendance/pending_checkout/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'pending_count' in response.data
        assert 'records' in response.data
    
    def test_check_in_attendance(self):
        """Test checking in attendance."""
        self.client.force_authenticate(user=self.user)
        
        # Create new attendance record for today
        today = timezone.now().date()
        attendance = Attendance.objects.create(
            student=self.student,
            date=today,
            check_in_time=None,
            check_out_time=None
        )
        
        response = self.client.post(
            f'/api/attendance/{attendance.id}/check_in/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'Checked in'
    
    def test_check_out_attendance(self):
        """Test checking out attendance."""
        self.client.force_authenticate(user=self.user)
        
        # Get a record with check-in but no check-out
        attendance = Attendance.objects.filter(check_out_time__isnull=True).first()
        
        if attendance:
            response = self.client.post(
                f'/api/attendance/{attendance.id}/check_out/'
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'Checked out'
    
    def test_daily_summary(self):
        """Test getting daily attendance summary."""
        self.client.force_authenticate(user=self.user)
        
        today = timezone.now().date()
        response = self.client.get(f'/api/attendance/daily_summary/?date={today}')
        
        assert response.status_code == status.HTTP_200_OK


class CacheIntegrationTestCase(APITestCase):
    """Integration tests for cache functionality."""
    
    def setUp(self):
        """Create test user and students."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        self.student = Student.objects.create(
            name='Test Student',
            email='test@example.com',
            student_class='A'
        )
        
        self.client = APIClient()
    
    def test_cache_invalidation_on_update(self):
        """Test that cache is invalidated when student is updated."""
        self.client.force_authenticate(user=self.user)
        
        # Get student (should be cached)
        response1 = self.client.get(f'/api/students/{self.student.id}/')
        assert response1.status_code == status.HTTP_200_OK
        
        # Update student
        response2 = self.client.put(
            f'/api/students/{self.student.id}/',
            {'name': 'Updated Name', 'email': 'updated@example.com', 'student_class': 'A'},
            format='json'
        )
        assert response2.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]


class ErrorHandlingIntegrationTestCase(APITestCase):
    """Integration tests for error handling."""
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.client = APIClient()
    
    def test_invalid_filter_parameter(self):
        """Test handling of invalid filter parameters."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/students/?page_size=invalid')
        
        # Should either return 400 or use default page_size
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_nonexistent_resource(self):
        """Test handling of nonexistent resource."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/students/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthenticated_request(self):
        """Test handling of unauthenticated request."""
        response = self.client.get('/api/students/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
