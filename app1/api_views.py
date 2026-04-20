"""REST API Views for AI Attendance System - Day 7: Advanced Features

This module provides enhanced ViewSets with pagination, filtering, ordering,
and bulk operations for the REST API endpoints.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework_filters import filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from app1.models import Student, Attendance
from app1.serializers import (
    StudentSerializer, StudentDetailSerializer, 
    AttendanceSerializer, AttendanceSummarySerializer
)
from app1.services import AttendanceService, FaceRecognitionService
from app1.cache_utils import CacheManager
from app1.face_enrollment import FaceEnrollmentMixin
from app1.notification_service import EmailNotificationService
from app1.analytics_service import AttendanceAnalyticsService
from app1.api_filters import StudentFilter, AttendanceFilter
from app1.api_pagination import (
    StandardPagination, StudentCursorPagination, 
    AttendanceCursorPagination, StandardOrdering
)
from app1.api_validators import (
    StudentDataValidator, AttendanceDataValidator, 
    BulkOperationValidator, QueryParamValidator
)
import logging

logger = logging.getLogger(__name__)


class StudentViewSet(FaceEnrollmentMixin, viewsets.ModelViewSet):
    """Enhanced ViewSet for Student model with filtering, pagination, and bulk operations."""

    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    # Pagination and filtering configuration
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = StudentFilter
    search_fields = ['name', 'email', 'student_class']
    ordering_fields = StandardOrdering.STUDENT_ORDERING_FIELDS
    ordering = StandardOrdering.STUDENT_DEFAULT_ORDERING

    def get_serializer_class(self):
        """Return detail serializer for retrieve action."""
        if self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentSerializer

    def get_queryset(self):
        """Optimize queryset with prefetch_related."""
        queryset = Student.objects.all()
        
        # Optimize for list views
        if self.action == 'list':
            queryset = queryset.prefetch_related('attendance_set')
        
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_authorize', 'send_bulk_reminders']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create student with validation."""
        try:
            name = StudentDataValidator.validate_name(serializer.validated_data.get('name', ''))
            email = StudentDataValidator.validate_email(serializer.validated_data.get('email', ''))
            serializer.save()
            logger.info(f"Student created: {name} ({email})")
        except Exception as e:
            logger.error(f"Error creating student: {str(e)}")
            raise

    def perform_update(self, serializer):
        """Update student with validation and cache clearing."""
        try:
            serializer.save()
            CacheManager.delete_student_cache(self.get_object().id)
            logger.info(f"Student updated: {serializer.instance.name}")
        except Exception as e:
            logger.error(f"Error updating student: {str(e)}")
            raise

    @action(detail=True, methods=['post'])
    def authorize(self, request, pk=None):
        """Authorize a student for face recognition."""
        student = self.get_object()
        student.authorized = True
        student.save()
        CacheManager.delete_student_cache(student.id)
        
        return Response(
            {'status': 'Student authorized', 'student': StudentSerializer(student).data},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def attendance_history(self, request, pk=None):
        """Get attendance history for a student with pagination."""
        student = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        try:
            QueryParamValidator.validate_page_size(request.query_params.get('page_size', 20))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        attendance_records = AttendanceService.get_student_attendance_history(student, days)
        
        # Paginate results
        paginator = StandardPagination()
        paginated_records = paginator.paginate_queryset(attendance_records, request)
        serializer = AttendanceSerializer(paginated_records, many=True)
        
        return paginator.get_paginated_response({
            'student': student.name,
            'days': days,
            'total_records': attendance_records.count(),
            'records': serializer.data
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get comprehensive summary statistics for all students."""
        total = Student.objects.count()
        authorized = Student.objects.filter(authorized=True).count()
        unauthorized = total - authorized
        
        # Calculate attendance rate
        avg_attendance = Attendance.objects.aggregate(Avg('id')).get('id__avg') or 0
        
        return Response({
            'total_students': total,
            'authorized': authorized,
            'unauthorized': unauthorized,
            'authorization_rate': round((authorized / total * 100) if total > 0 else 0, 2),
            'timestamp': datetime.now().isoformat()
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def bulk_authorize(self, request):
        """Bulk authorize students with validation."""
        try:
            student_ids = BulkOperationValidator.validate_bulk_ids(request.data.get('student_ids', []))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Student.objects.filter(id__in=student_ids, authorized=False)
        updated = queryset.update(authorized=True)
        
        # Clear cache for updated students
        for student_id in queryset.values_list('id', flat=True):
            CacheManager.delete_student_cache(student_id)
        
        total_authorized = Student.objects.filter(authorized=True).count()
        total_students = Student.objects.count()
        
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
        """Send attendance reminder email to student."""
        student = self.get_object()
        result = EmailNotificationService.send_attendance_reminder(student)
        
        return Response({
            'success': result,
            'message': f'Reminder email sent to {student.email}' if result else 'Failed to send reminder'
        }, status=status.HTTP_200_OK if result else status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def send_bulk_reminders(self, request):
        """Send bulk reminder notifications to students."""
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
        
        logger.info(f"Sent {success_count} reminders, {failed_count} failed")
        
        return Response({
            'success': True,
            'success_count': success_count,
            'failed_count': failed_count,
            'total': success_count + failed_count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def bulk_delete(self, request):
        """Delete multiple students by IDs."""
        try:
            student_ids = BulkOperationValidator.validate_bulk_ids(request.data.get('student_ids', []))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Student.objects.filter(id__in=student_ids)
        count = queryset.count()
        
        # Clear cache before deletion
        for student_id in student_ids:
            CacheManager.delete_student_cache(student_id)
        
        queryset.delete()
        logger.info(f"Bulk deleted {count} students")
        
        return Response({
            'success': True,
            'deleted_count': count
        }, status=status.HTTP_200_OK)


class AttendanceViewSet(viewsets.ModelViewSet):
    """Enhanced ViewSet for Attendance model with filtering, pagination, and analytics."""

    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    # Pagination and filtering configuration
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AttendanceFilter
    search_fields = ['student__name', 'student__email']
    ordering_fields = StandardOrdering.ATTENDANCE_ORDERING_FIELDS
    ordering = StandardOrdering.ATTENDANCE_DEFAULT_ORDERING

    def get_queryset(self):
        """Optimize queryset with select_related."""
        queryset = Attendance.objects.all()
        
        # Optimize for list views
        if self.action == 'list':
            queryset = queryset.select_related('student')
        
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_checkout']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

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
        return Response({'error': 'Cannot check in'}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({'error': 'Cannot check out'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily attendance summary."""
        date_str = request.query_params.get('date')
        summary = AttendanceService.get_daily_attendance_summary(date_str)
        serializer = AttendanceSummarySerializer(summary)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_checkout(self, request):
        """Get all students pending checkout."""
        pending = Attendance.objects.filter(
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).select_related('student')
        
        # Paginate results
        paginator = StandardPagination()
        paginated_records = paginator.paginate_queryset(pending, request)
        serializer = AttendanceSerializer(paginated_records, many=True)
        
        return paginator.get_paginated_response({
            'pending_count': pending.count(),
            'records': serializer.data
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def bulk_checkout(self, request):
        """Bulk checkout multiple students."""
        try:
            attendance_ids = BulkOperationValidator.validate_bulk_ids(request.data.get('attendance_ids', []))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Attendance.objects.filter(
            id__in=attendance_ids,
            check_out_time__isnull=True
        )
        
        updated = 0
        for attendance in queryset:
            result = AttendanceService.mark_check_out(attendance.student, attendance.date)
            if result:
                updated += 1
        
        logger.info(f"Bulk checked out {updated} attendances")
        
        return Response({
            'success': True,
            'checkout_count': updated,
            'total_requested': len(attendance_ids)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def bulk_delete(self, request):
        """Delete multiple attendance records."""
        try:
            attendance_ids = BulkOperationValidator.validate_bulk_ids(request.data.get('attendance_ids', []))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Attendance.objects.filter(id__in=attendance_ids)
        count = queryset.count()
        queryset.delete()
        
        logger.info(f"Bulk deleted {count} attendance records")
        
        return Response({
            'success': True,
            'deleted_count': count
        }, status=status.HTTP_200_OK)


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
        ).select_related('student').order_by('-date')[:10]
        
        data = serializer.data
        data['recent_attendance'] = AttendanceSerializer(recent_attendance, many=True).data
        
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, student_id):
        """Update student details."""
        student = get_object_or_404(Student, pk=student_id)
        serializer = StudentSerializer(student, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            CacheManager.delete_student_cache(student.id)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from datetime import datetime
