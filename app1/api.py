"""
RESTful API endpoints for attendance system
Provides comprehensive API for mobile and external integrations
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from app1.models import Student, Attendance
from app1.serializers import StudentSerializer, AttendanceSerializer
from app1.search_service import AttendanceSearchService
from app1.batch_processor import BatchProcessor
import logging

logger = logging.getLogger(__name__)


class StudentAPIViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Student operations
    Supports CRUD operations and advanced filtering
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter students based on query parameters"""
        queryset = super().get_queryset()

        # Search by name or roll number
        search = self.request.query_params.get('search', None)
        if search:
            queryset = AttendanceSearchService.search_students(search)

        # Filter by class/department
        class_filter = self.request.query_params.get('class', None)
        if class_filter:
            queryset = queryset.filter(student_class__icontains=class_filter)

        # Filter by authorization status
        authorized = self.request.query_params.get('authorized', None)
        if authorized is not None:
            queryset = queryset.filter(authorized=authorized.lower() == 'true')

        return queryset

    @action(detail=False, methods=['post'])
    def authorize_students(self, request):
        """Bulk authorize students"""
        department = request.data.get('department', None)
        max_count = request.data.get('max_count', None)

        result = BatchProcessor.authorize_students_batch(
            department=department,
            max_count=max_count
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def send_notifications(self, request):
        """Send bulk notifications to students"""
        notification_type = request.data.get('type', 'reminder')
        authorized_only = request.data.get('authorized_only', False)
        department = request.data.get('department', None)

        result = BatchProcessor.send_notifications_batch(
            notification_type=notification_type,
            authorized_only=authorized_only,
            department=department
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def attendance_summary(self, request, pk=None):
        """Get attendance summary for a student"""
        student = self.get_object()
        attendance_data = Attendance.objects.filter(student=student)

        summary = {
            'student_id': student.id,
            'name': student.name,
            'total_records': attendance_data.count(),
            'present': attendance_data.filter(
                status='Present'
            ).count(),
            'absent': attendance_data.filter(
                status='Absent'
            ).count(),
            'late': attendance_data.filter(
                status='Late'
            ).count()
        }

        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def delete_with_cascade(self, request, pk=None):
        """Delete student and associated records"""
        student = self.get_object()
        student_name = student.name

        try:
            Attendance.objects.filter(student=student).delete()
            student.delete()

            return Response(
                {'message': f'Student {student_name} deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Error deleting student: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AttendanceAPIViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Attendance operations
    Supports complex queries and bulk operations
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Advanced filtering for attendance records"""
        queryset = super().get_queryset()

        # Date range filtering
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date and end_date:
            queryset = AttendanceSearchService.search_attendance({
                'start_date': start_date,
                'end_date': end_date
            })

        # Status filtering
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Student filtering
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        return queryset.order_by('-date', '-check_in_time')

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Bulk update attendance status"""
        date_filter = request.data.get('date', None)
        new_status = request.data.get('status', None)

        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        def update_status(record):
            record.status = new_status
            record.save()

        result = BatchProcessor.update_attendance_status_batch(
            date_filter=date_filter,
            status_update_func=update_status
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """Export attendance data"""
        export_type = request.query_params.get('type', 'attendance')
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date

        result = BatchProcessor.bulk_export_data(
            export_type=export_type,
            filters=filters
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def cleanup_duplicates(self, request):
        """Clean up duplicate records"""
        result = BatchProcessor.cleanup_duplicate_records()
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get attendance statistics"""
        total_records = Attendance.objects.count()
        today_records = Attendance.objects.filter(
            date__date=__import__('datetime').date.today()
        ).count()

        stats = {
            'total_attendance_records': total_records,
            'today_records': today_records,
            'by_status': {
                'present': Attendance.objects.filter(status='Present').count(),
                'absent': Attendance.objects.filter(status='Absent').count(),
                'late': Attendance.objects.filter(status='Late').count()
            },
            'students_count': Student.objects.count(),
            'authorized_count': Student.objects.filter(authorized=True).count()
        }

        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def detailed_report(self, request, pk=None):
        """Get detailed report for specific attendance record"""
        record = self.get_object()

        try:
            report = {
                'id': record.id,
                'student': StudentSerializer(record.student).data,
                'date': record.date,
                'status': record.status,
                'check_in_time': record.check_in_time,
                'check_out_time': record.check_out_time,
                'duration': str(
                    record.check_out_time - record.check_in_time
                ) if record.check_out_time else None,
                'notes': record.notes if hasattr(record, 'notes') else None
            }
            return Response(report, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DashboardAPIView:
    """Dashboard API endpoints for analytics and summaries"""

    @staticmethod
    def get_dashboard_data(request):
        """Comprehensive dashboard data"""
        try:
            from django.db.models import Count, Q
            from datetime import date, timedelta

            today = date.today()
            week_ago = today - timedelta(days=7)

            dashboard = {
                'today': {
                    'total_check_ins': Attendance.objects.filter(
                        date=today
                    ).count(),
                    'present': Attendance.objects.filter(
                        date=today,
                        status='Present'
                    ).count(),
                    'absent': Attendance.objects.filter(
                        date=today,
                        status='Absent'
                    ).count(),
                    'late': Attendance.objects.filter(
                        date=today,
                        status='Late'
                    ).count()
                },
                'week': {
                    'total_records': Attendance.objects.filter(
                        date__gte=week_ago
                    ).count(),
                    'unique_students': Attendance.objects.filter(
                        date__gte=week_ago
                    ).values('student').distinct().count()
                },
                'total_students': Student.objects.count(),
                'authorized_students': Student.objects.filter(
                    authorized=True
                ).count(),
                'recent_check_ins': AttendanceSearchService.search_attendance({
                    'limit': 5
                })
            }

            return Response(dashboard, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
