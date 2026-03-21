from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Sum

from .models import Student, Attendance, CameraConfiguration, AttendanceSummary, AttendanceAlert
from .serializers import (
    StudentSerializer, AttendanceSerializer, CameraConfigSerializer,
    AttendanceSummarySerializer, AttendanceAlertSerializer, AttendanceDetailedSerializer
)


class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Student CRUD operations
    """
    queryset = Student.objects.all().order_by('-created_at')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['authorized', 'student_class']
    search_fields = ['name', 'email', 'student_class']
    ordering_fields = ['name', 'created_at', '-created_at']

    @action(detail=True, methods=['get'])
    def attendance_details(self, request, pk=None):
        """Get detailed attendance for a student"""
        student = self.get_object()
        days = request.query_params.get('days', 30)
        
        start_date = timezone.now().date() - timedelta(days=int(days))
        attendance = Attendance.objects.filter(
            student=student,
            date__gte=start_date
        ).order_by('-date')
        
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def low_attendance(self, request):
        """Get students with low attendance"""
        threshold = request.query_params.get('threshold', 75)
        students = Student.objects.filter(authorized=True)
        
        low_attendance_students = [
            s for s in students 
            if s.get_attendance_percentage() < float(threshold)
        ]
        
        serializer = self.get_serializer(low_attendance_students, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def authorize(self, request, pk=None):
        """Authorize a student"""
        student = self.get_object()
        student.authorized = True
        student.save()
        return Response({'status': 'Student authorized'})

    @action(detail=True, methods=['post'])
    def deauthorize(self, request, pk=None):
        """Deauthorize a student"""
        student = self.get_object()
        student.authorized = False
        student.save()
        return Response({'status': 'Student deauthorized'})


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Attendance CRUD operations
    """
    queryset = Attendance.objects.all().order_by('-date')
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'date', 'status']
    search_fields = ['student__name', 'status']
    ordering_fields = ['date', 'check_in_time', '-date']

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's attendance"""
        today = timezone.now().date()
        attendance = Attendance.objects.filter(date=today)
        serializer = self.get_serializer(attendance, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def present_today(self, request):
        """Get students present today"""
        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            date=today,
            check_in_time__isnull=False
        )
        serializer = self.get_serializer(attendance, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def absent_today(self, request):
        """Get students absent today"""
        today = timezone.now().date()
        present_students = Attendance.objects.filter(
            date=today,
            check_in_time__isnull=False
        ).values_list('student_id', flat=True)
        
        absent_students = Student.objects.filter(
            authorized=True
        ).exclude(id__in=present_students)
        
        serializer = StudentSerializer(absent_students, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get attendance for date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        student_id = request.query_params.get('student_id')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query = Attendance.objects.filter(
            date__range=[start_date, end_date]
        )
        
        if student_id:
            query = query.filter(student_id=student_id)
        
        serializer = self.get_serializer(query, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """Bulk import attendance records"""
        records = request.data  # Expecting list of attendance records
        
        created_records = []
        for record in records:
            attendance, created = Attendance.objects.get_or_create(
                student_id=record.get('student_id'),
                date=record.get('date')
            )
            if created:
                attendance.status = record.get('status', 'absent')
                attendance.save()
                created_records.append(AttendanceSerializer(attendance).data)
        
        return Response({
            'created': len(created_records),
            'records': created_records
        })


class CameraConfigViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Camera Configuration CRUD operations
    """
    queryset = CameraConfiguration.objects.all().order_by('name')
    serializer_class = CameraConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate camera"""
        camera = self.get_object()
        camera.is_active = True
        camera.save()
        return Response({'status': 'Camera activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate camera"""
        camera = self.get_object()
        camera.is_active = False
        camera.save()
        return Response({'status': 'Camera deactivated'})


class AttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Attendance Summary (read-only)
    """
    queryset = AttendanceSummary.objects.all().order_by('-month')
    serializer_class = AttendanceSummarySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'month']
    search_fields = ['student__name']
    ordering_fields = ['month', 'percentage', '-percentage']

    @action(detail=False, methods=['get'])
    def current_month(self, request):
        """Get attendance summary for current month"""
        today = timezone.now()
        current_month = today.strftime('%Y-%m')
        
        summaries = AttendanceSummary.objects.filter(month=current_month)
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def student_summary(self, request):
        """Get attendance summary for a specific student"""
        student_id = request.query_params.get('student_id')
        months = request.query_params.get('months', 6)
        
        if not student_id:
            return Response(
                {'error': 'student_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        summaries = AttendanceSummary.objects.filter(
            student_id=student_id
        ).order_by('-month')[:int(months)]
        
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)


class AttendanceAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Attendance Alerts
    """
    queryset = AttendanceAlert.objects.all().order_by('-created_at')
    serializer_class = AttendanceAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'alert_type', 'is_sent']
    ordering_fields = ['created_at', 'sent_at']

    @action(detail=False, methods=['get'])
    def unsent(self, request):
        """Get unsent alerts"""
        alerts = AttendanceAlert.objects.filter(is_sent=False).order_by('-created_at')
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        """Mark alert as sent"""
        alert = self.get_object()
        alert.is_sent = True
        alert.sent_at = timezone.now()
        alert.save()
        return Response({'status': 'Alert marked as sent'})

    @action(detail=False, methods=['post'])
    def send_pending_alerts(self, request):
        """Mark all pending alerts as sent (for email task trigger)"""
        alerts = AttendanceAlert.objects.filter(is_sent=False)
        count = alerts.count()
        alerts.update(is_sent=True, sent_at=timezone.now())
        return Response({'sent': count})
