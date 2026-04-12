"""
API INTEGRATION GUIDE
=====================

This guide shows how to integrate the REST API endpoints into your Django project.

STEP 1: Install Django REST Framework
--------------------------------------
pip install djangorestframework


STEP 2: Update settings.py
---------------------------
Add to INSTALLED_APPS:
    INSTALLED_APPS = [
        ...
        'rest_framework',
        'app1',
    ]

Add REST Framework configuration:
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.SessionAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_FILTER_BACKENDS': [
            'rest_framework.filters.SearchFilter',
            'rest_framework.filters.OrderingFilter',
        ],
    }


STEP 3: Update Project URLs (Project101/urls.py)
-------------------------------------------------
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app1.api_urls import router  # Import the router

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app1.urls')),
    path('api/v1/', include(router.urls)),  # Add this line
    path('api-auth/', include('rest_framework.urls')),  # Add this line
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


STEP 4: Run Migrations
----------------------
python manage.py migrate


STEP 5: Test the API
---------------------
The API will be available at:
    http://localhost:8000/api/v1/students/
    http://localhost:8000/api/v1/attendance/

You can use:
- Browser: Visit the URLs directly
- cURL: curl http://localhost:8000/api/v1/students/
- Postman: Import the endpoints
- Python requests: requests.get('http://localhost:8000/api/v1/students/')


AVAILABLE ENDPOINTS
====================

1. Students Management:
   GET     /api/v1/students/                      - List all students
   POST    /api/v1/students/                      - Create student
   GET     /api/v1/students/{id}/                 - Get student details
   PUT     /api/v1/students/{id}/                 - Update student
   DELETE  /api/v1/students/{id}/                 - Delete student
   POST    /api/v1/students/{id}/authorize/       - Authorize student
   GET     /api/v1/students/{id}/attendance_history/  - Get attendance history
   GET     /api/v1/students/summary/              - Get students summary

2. Attendance Management:
   GET     /api/v1/attendance/                    - List attendance records
   POST    /api/v1/attendance/                    - Create attendance
   GET     /api/v1/attendance/{id}/               - Get attendance record
   PUT     /api/v1/attendance/{id}/               - Update attendance
   DELETE  /api/v1/attendance/{id}/               - Delete attendance
   POST    /api/v1/attendance/{id}/check_in/     - Check in student
   POST    /api/v1/attendance/{id}/check_out/    - Check out student
   GET     /api/v1/attendance/daily_summary/     - Daily summary
   GET     /api/v1/attendance/pending_checkout/  - Pending checkouts

3. Custom Endpoints:
   GET     /api/v1/students/{id}/details/        - Detailed student info

4. Authentication:
   GET     /api-auth/login/                       - Login page
   GET     /api-auth/logout/                      - Logout


QUERY PARAMETERS
================

Students:
- ?authorized=true|false      - Filter by authorization status
- ?search=john                - Search by name/email
- ?page=2&page_size=10        - Pagination

Attendance:
- ?student_id=1               - Filter by student
- ?date_from=2024-01-01       - Filter by start date
- ?date_to=2024-01-31         - Filter by end date
- ?status=checked_in|checked_out - Filter by status
- ?page=2&page_size=10        - Pagination


AUTHENTICATION
===============

All endpoints require authentication. Use SessionAuthentication:

1. Login via admin:
   http://localhost:8000/admin/

2. Then use the authenticated session to access API

3. Include credentials in requests:
   requests.get('http://localhost:8000/api/v1/students/', 
                auth=('username', 'password'))


CORS SETUP (Optional)
=======================

If you need CORS for frontend access, install:
    pip install django-cors-headers

Then add to settings.py:
    INSTALLED_APPS = [
        ...
        'corsheaders',
    ]

    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        ...
    ]

    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:8000',
    ]
"""
