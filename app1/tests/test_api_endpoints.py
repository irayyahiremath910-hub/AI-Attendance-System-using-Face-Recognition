"""
Tests for REST API Endpoints
"""

import pytest
from rest_framework import status
from app1.models import Student, Attendance
from datetime import date


class TestStudentAPI:
    """Test cases for Student API endpoints"""

    def test_list_students(self, authenticated_client):
        """Test listing all students"""
        response = authenticated_client.get('/api/students/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_students_unauthorized(self, api_client):
        """Test listing students without authentication"""
        response = api_client.get('/api/students/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_student_admin(self, authenticated_client):
        """Test creating student as admin"""
        data = {
            'name': 'New Student',
            'email': 'new@example.com',
            'phone_number': '1234567890',
            'student_class': 'CSE',
            'authorized': False
        }
        response = authenticated_client.post('/api/students/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_student(self, authenticated_client, test_student):
        """Test retrieving single student"""
        response = authenticated_client.get(f'/api/students/{test_student.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == test_student.name

    def test_filter_authorized_students(self, authenticated_client):
        """Test filtering by authorized status"""
        response = authenticated_client.get('/api/students/?authorized=true')
        assert response.status_code == status.HTTP_200_OK

    def test_authorization_status_field(self, authenticated_client, test_student):
        """Test student has authorization field"""
        response = authenticated_client.get(f'/api/students/{test_student.id}/')
        assert 'authorized' in response.data

    def test_face_status_endpoint(self, authenticated_client, test_student):
        """Test student face status endpoint"""
        response = authenticated_client.get(f'/api/students/{test_student.id}/face_status/')
        assert response.status_code == status.HTTP_200_OK
        assert 'ready_for_attendance' in response.data


class TestAttendanceAPI:
    """Test cases for Attendance API endpoints"""

    def test_list_attendance(self, authenticated_client):
        """Test listing attendance records"""
        response = authenticated_client.get('/api/attendances/')
        assert response.status_code == status.HTTP_200_OK

    def test_daily_summary_endpoint(self, authenticated_client, test_attendance):
        """Test daily attendance summary"""
        response = authenticated_client.get('/api/attendances/daily_summary/')
        assert response.status_code == status.HTTP_200_OK

    def test_pending_checkout_endpoint(self, authenticated_client, test_attendance):
        """Test pending checkout endpoint"""
        response = authenticated_client.get('/api/attendances/pending_checkout/')
        assert response.status_code == status.HTTP_200_OK
        assert 'pending_count' in response.data

    def test_filter_attendance_by_student(self, authenticated_client, test_attendance):
        """Test filtering attendance by student"""
        response = authenticated_client.get(
            f'/api/attendances/?student_id={test_attendance.student.id}'
        )
        assert response.status_code == status.HTTP_200_OK


class TestAuthorizationAPI:
    """Test cases for authorization endpoints"""

    def test_authorize_student_endpoint(self, authenticated_client, test_unauthorized_student):
        """Test authorize student endpoint"""
        response = authenticated_client.post(
            f'/api/students/{test_unauthorized_student.id}/authorize/'
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify authorization
        test_unauthorized_student.refresh_from_db()
        assert test_unauthorized_student.authorized is True

    def test_bulk_authorize_students(self, authenticated_client, db):
        """Test bulk authorization endpoint"""
        # Create multiple unauthorized students
        for i in range(5):
            Student.objects.create(
                name=f'Student {i}',
                email=f'student{i}@example.com',
                phone_number=f'123456789{i}',
                student_class='CSE',
                authorized=False
            )
        
        data = {'count': 3}
        response = authenticated_client.post('/api/students/bulk_authorize/', data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['authorized_count'] == 3

    def test_bulk_authorize_with_face_required(self, authenticated_client, db):
        """Test bulk authorization with face requirement"""
        # Create student with face encoding
        student = Student.objects.create(
            name='Student With Face',
            email='face@example.com',
            phone_number='1234567890',
            student_class='CSE',
            authorized=False,
            face_encoding=[0.1] * 128
        )
        
        data = {'count': 1, 'face_required': True}
        response = authenticated_client.post('/api/students/bulk_authorize/', data)
        assert response.status_code == status.HTTP_200_OK


class TestSummaryAPI:
    """Test cases for summary endpoints"""

    def test_student_summary(self, authenticated_client, test_student, test_unauthorized_student):
        """Test student summary endpoint"""
        response = authenticated_client.get('/api/students/summary/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_students' in response.data
        assert 'authorized' in response.data
        assert 'authorization_rate' in response.data
