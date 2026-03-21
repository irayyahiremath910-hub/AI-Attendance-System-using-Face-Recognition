from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    StudentViewSet, AttendanceViewSet, CameraConfigViewSet,
    AttendanceSummaryViewSet, AttendanceAlertViewSet
)

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student-api')
router.register(r'attendance', AttendanceViewSet, basename='attendance-api')
router.register(r'camera-config', CameraConfigViewSet, basename='camera-config-api')
router.register(r'attendance-summary', AttendanceSummaryViewSet, basename='attendance-summary-api')
router.register(r'alerts', AttendanceAlertViewSet, basename='alert-api')

app_name = 'api'

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('rest_framework.urls')),
]
