"""
Pytest configuration and fixtures for AI Attendance System tests
"""

import pytest
from django.contrib.auth.models import User
from app1.models import Student, Attendance
from django.utils import timezone
from datetime import datetime, date
import os


@pytest.fixture
def django_db_setup(django_db_setup, django_db_blocker):
    """Configure Django test database"""
    with django_db_blocker.unblock():
        pass


@pytest.fixture
def test_student(db):
    """Create a test student"""
    return Student.objects.create(
        name='Test Student',
        email='test@example.com',
        phone_number='1234567890',
        student_class='CSE',
        authorized=True
    )


@pytest.fixture
def test_unauthorized_student(db):
    """Create an unauthorized test student"""
    return Student.objects.create(
        name='Unauthorized Student',
        email='unauth@example.com',
        phone_number='9876543210',
        student_class='CIVIL',
        authorized=False
    )


@pytest.fixture
def test_attendance(db, test_student):
    """Create test attendance record"""
    attendance = Attendance.objects.create(
        student=test_student,
        date=date.today()
    )
    attendance.mark_checked_in()
    return attendance


@pytest.fixture
def admin_user(db):
    """Create admin user for API tests"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )


@pytest.fixture
def regular_user(db):
    """Create regular user for API tests"""
    user = User.objects.create_user(
        username='user',
        email='user@example.com',
        password='user123'
    )
    return user


@pytest.fixture
def api_client():
    """Return DRF API client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return authenticated API client"""
    api_client.force_authenticate(user=admin_user)
    return api_client
