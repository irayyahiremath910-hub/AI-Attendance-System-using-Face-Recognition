from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Home & Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Student Management
    path('capture_student/', views.capture_student, name='capture_student'),
    path('selfie-success/', views.selfie_success, name='selfie_success'),
    path('students/', views.student_list, name='student-list'),
    path('students/<int:pk>/', views.student_detail, name='student-detail'),
    path('students/<int:pk>/authorize/', views.student_authorize, name='student-authorize'),
    path('students/<int:pk>/delete/', views.student_delete, name='student-delete'),
    
    # Attendance
    path('capture-and-recognize/', views.capture_and_recognize, name='capture_and_recognize'),
    path('students/attendance/', views.student_attendance_list, name='student_attendance_list'),
    
    # Reports & Analytics
    path('attendance-report/', views.attendance_report, name='attendance_report'),
    path('low-attendance-students/', views.low_attendance_students, name='low_attendance_students'),
    
    # Export
    path('export/attendance/csv/', views.export_attendance_csv, name='export_attendance_csv'),
    path('export/attendance/pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),
    
    # Camera Configuration
    path('camera-config/', views.camera_config_create, name='camera_config_create'),
    path('camera-config/list/', views.camera_config_list, name='camera_config_list'),
    path('camera-config/update/<int:pk>/', views.camera_config_update, name='camera_config_update'),
    path('camera-config/delete/<int:pk>/', views.camera_config_delete, name='camera_config_delete'),
]
    

