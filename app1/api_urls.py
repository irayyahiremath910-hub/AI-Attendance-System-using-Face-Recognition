"""API URL Configuration for AI Attendance System

This module defines REST API endpoints for the attendance system.
Include this in your main urls.py with:

    from rest_framework.routers import DefaultRouter
    from app1.api_urls import router
    
    urlpatterns = [
        path('api/', include(router.urls)),
    ]
"""

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .api_views import StudentViewSet, AttendanceViewSet, StudentDetailView

# Create a router for automatic URL generation from viewsets
router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

# Additional custom endpoints
urlpatterns = [
    # Auto-generated routes from ViewSets
    path('', include(router.urls)),
    
    # Custom endpoints
    path('students/<int:student_id>/details/', StudentDetailView.as_view(), name='student-details'),
    
    # Authentication
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

"""
API ENDPOINTS DOCUMENTATION
============================

1. Students Endpoints:
   - GET    /api/students/              - List all students
   - POST   /api/students/              - Create new student
   - GET    /api/students/{id}/         - Retrieve specific student
   - PUT    /api/students/{id}/         - Update student
   - PATCH  /api/students/{id}/         - Partial update
   - DELETE /api/students/{id}/         - Delete student
   - GET    /api/students/{id}/details/ - Student with attendance history

2. Attendance Endpoints:
   - GET    /api/attendance/            - List all attendance records
   - POST   /api/attendance/            - Create attendance record
   - GET    /api/attendance/{id}/       - Retrieve specific record
   - PUT    /api/attendance/{id}/       - Update record
   - DELETE /api/attendance/{id}/       - Delete record

3. Filter Options (Query Parameters):
   - /api/students/?authorized=true    - Filter by authorization status
   - /api/attendance/?student_id=1     - Filter by student
   - /api/attendance/?date=2024-01-15  - Filter by date
   - /api/attendance/?check_in_time__isnull=false - Checked in students

4. Pagination:
   - Add ?page=2&page_size=20 to any list endpoint

5. Search:
   - /api/students/?search=john        - Search students by name/email

EXAMPLE REQUESTS:
=================

Create a new student:
    POST /api/students/
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone_number": "9876543210",
        "student_class": "A"
    }

Mark attendance check-in:
    POST /api/attendance/
    {
        "student": 1,
        "date": "2024-01-15",
        "check_in_time": "2024-01-15T09:00:00Z"
    }

Get student with attendance history:
    GET /api/students/1/details/

Response:
    {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone_number": "9876543210",
        "student_class": "A",
        "authorized": false,
        "created_at": "2024-01-15T08:00:00Z",
        "total_attendance": 5,
        "latest_attendance": {
            "id": 1,
            "student": 1,
            "student_name": "John Doe",
            "date": "2024-01-15",
            "check_in_time": "2024-01-15T09:00:00Z",
            "check_out_time": "2024-01-15T17:30:00Z",
            "duration": "8h 30m"
        }
    }
"""
