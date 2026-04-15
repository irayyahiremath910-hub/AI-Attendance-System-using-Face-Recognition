"""REST API Views for AI Attendance System

This module provides ViewSets and Views for the REST API endpoints.
These views use the service layer and serializers for clean, maintainable code.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from app1.models import Student, Attendance
from app1.serializers import StudentSerializer, StudentDetailSerializer, AttendanceSerializer, AttendanceSummarySerializer
from app1.services import AttendanceService, FaceRecognitionService
from app1.cache_utils import CacheManager
from app1.face_enrollment import FaceEnrollmentMixin
from app1.notification_service import EmailNotificationService
from app1.analytics_service import AttendanceAnalyticsService
import logging

logger = logging.getLogger(__name__)


class StudentViewSet(FaceEnrollmentMixin, viewsets.ModelViewSet):
    """ViewSet for Student model with full CRUD operations and face enrollment."""

    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_class(self):
        """Return detail serializer for retrieve action."""
        if self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = Student.objects.all()
        
        # Filter by authorization status
        authorized = self.request.query_params.get('authorized')
        if authorized is not None:
            authorized_bool = authorized.lower() == 'true'
            queryset = queryset.filter(authorized=authorized_bool)
        
        # Search by name or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def authorize(self, request, pk=None):
        """Authorize a student for face recognition."""
        student = self.get_object()
        student.authorized = True
        student.save()
        
        # Clear cache when authorizing
        CacheManager.delete_student_cache(student.id)
        
        return Response(
            {'status': 'Student authorized', 'student': StudentSerializer(student).data},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def attendance_history(self, request, pk=None):
        """Get attendance history for a student."""
        student = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        attendance_records = AttendanceService.get_student_attendance_history(student, days)
        serializer = AttendanceSerializer(attendance_records, many=True)
        
        return Response({
            'student': student.name,
            'days': days,
            'records': serializer.data,
            'total': attendance_records.count()
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for all students."""
        total = Student.objects.count()
        authorized = Student.objects.filter(authorized=True).count()
        unauthorized = Student.objects.filter(authorized=False).count()
        
        return Response({
            'total_students': total,
            'authorized': authorized,
            'unauthorized': unauthorized,
            'authorization_rate': round((authorized / total * 100) if total > 0 else 0, 2)
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def bulk_authorize(self, request):
        """Bulk authorize students"""
        count = request.data.get('count', 10)
        face_required = request.data.get('face_required', False)
        
        queryset = Student.objects.filter(authorized=False)
        
        if face_required:
            queryset = queryset.exclude(face_encoding__isnull=True)
        
        queryset = queryset[:count]
        total = queryset.count()
        
        if total == 0:
            return Response({
                'error': 'No students found matching criteria'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        updated = queryset.update(authorized=True)
        
        total_authorized = Student.objects.filter(authorized=True).count()
        total_students = Student.objects.count()
        
        # Clear cache for updated students
        for student_id in queryset.values_list('id', flat=True):
            CacheManager.delete_student_cache(student_id)
        
        logger.info(f"Bulk authorized {updated} students via API")
        
        return Response({
            'success': True,
            'authorized_count': updated,
            'total_authorized': total_authorized,
            'total_students': total_students,
            'authorization_rate': round((total_authorized / total_students * 100) if total_students > 0 else 0, 2)
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def send_reminder(self, request, pk=None):
        """Send attendance reminder email to student"""
        student = self.get_object()
        result = EmailNotificationService.send_attendance_reminder(student)
        
        if result:
            return Response({
                'success': True,
                'message': f'Reminder email sent to {student.email}'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to send reminder email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def send_report(self, request, pk=None):
        """Send attendance report email to student"""
        student = self.get_object()
        days = request.data.get('days', 7)
        result = EmailNotificationService.send_attendance_report(student, days)
        
        if result:
            return Response({
                'success': True,
                'message': f'Attendance report sent to {student.email}'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to send report email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def send_bulk_reminders(self, request):
        """Send bulk reminder notifications"""
        authorized_only = request.data.get('authorized_only', True)
        
        queryset = Student.objects.all()
        if authorized_only:
            queryset = queryset.filter(authorized=True)
        
        success_count = 0
        failed_count = 0
        
        for student in queryset:
            if EmailNotificationService.send_attendance_reminder(student):
                success_count += 1
            else:
                failed_count += 1
        
        return Response({
            'success': True,
            'success_count': success_count,
            'failed_count': failed_count,
            'total': success_count + failed_count
        }, status=status.HTTP_200_OK)


        # Filter by student
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by date
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'checked_in':
            queryset = queryset.filter(check_in_time__isnull=False, check_out_time__isnull=True)
        elif status_filter == 'checked_out':
            queryset = queryset.filter(check_out_time__isnull=False)
        
        return queryset.order_by('-date')

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Mark student as checked in."""
        attendance = self.get_object()
        result = AttendanceService.mark_check_in(attendance.student, attendance.date)
        
        if result:
            return Response(
                {'status': 'Checked in', 'attendance': AttendanceSerializer(result).data},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Cannot check in'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        """Mark student as checked out."""
        attendance = self.get_object()
        result = AttendanceService.mark_check_out(attendance.student, attendance.date)
        
        if result:
            return Response(
                {'status': 'Checked out', 'attendance': AttendanceSerializer(result).data},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Cannot check out'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily attendance summary."""
        date = request.query_params.get('date')
        summary = AttendanceService.get_daily_attendance_summary(date)
        serializer = AttendanceSummarySerializer(summary)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_checkout(self, request):
        """Get all students pending checkout."""
        from django.db.models import Q
        pending = Attendance.objects.filter(
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).select_related('student')
        
        serializer = AttendanceSerializer(pending, many=True)
        return Response({
            'pending_count': pending.count(),
            'records': serializer.data
        })


class StudentDetailView(APIView):
    """Custom view for detailed student information with attendance."""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        """Get student details with full attendance history."""
        student = get_object_or_404(Student, pk=student_id)
        serializer = StudentDetailSerializer(student)
        
        # Add recent attendance records
        recent_attendance = Attendance.objects.filter(
            student=student
        ).order_by('-date')[:10]
        
        data = serializer.data
        data['recent_attendance'] = AttendanceSerializer(recent_attendance, many=True).data
        
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, student_id):
        """Update student details."""
        student = get_object_or_404(Student, pk=student_id)
        serializer = StudentSerializer(student, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            # Clear cache when updating
            CacheManager.delete_student_cache(student.id)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
