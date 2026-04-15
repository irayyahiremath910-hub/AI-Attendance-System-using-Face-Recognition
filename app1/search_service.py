"""
Advanced search and filtering service for attendance and student data
Provides complex query building and export capabilities
"""

from app1.models import Student, Attendance
from django.db.models import Q, F, Count
from datetime import datetime, date
from django.http import HttpResponse
import csv
import logging

logger = logging.getLogger(__name__)


class AttendanceSearchService:
    """Service for advanced search and filtering of attendance records"""

    @staticmethod
    def search_students(query, filters=None):
        """Advanced student search with multiple filters"""
        queryset = Student.objects.all()

        # General search by name or email
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone_number__icontains=query)
            )

        # Apply filters
        if filters:
            if 'authorized' in filters:
                queryset = queryset.filter(authorized=filters['authorized'])

            if 'face_recognized' in filters:
                queryset = queryset.filter(face_recognized=filters['face_recognized'])

            if 'department' in filters:
                queryset = queryset.filter(
                    student_class__icontains=filters['department']
                )

            if 'created_after' in filters:
                queryset = queryset.filter(
                    created_at__gte=datetime.fromisoformat(filters['created_after'])
                )

            if 'created_before' in filters:
                queryset = queryset.filter(
                    created_at__lte=datetime.fromisoformat(filters['created_before'])
                )

        return queryset.order_by('-created_at')

    @staticmethod
    def search_attendance(filters):
        """Advanced attendance record search"""
        queryset = Attendance.objects.all()

        # Date range
        if 'date_from' in filters:
            queryset = queryset.filter(
                date__gte=datetime.fromisoformat(filters['date_from']).date()
            )

        if 'date_to' in filters:
            queryset = queryset.filter(
                date__lte=datetime.fromisoformat(filters['date_to']).date()
            )

        # Student filter
        if 'student_id' in filters:
            queryset = queryset.filter(student_id=filters['student_id'])

        if 'student_name' in filters:
            queryset = queryset.filter(
                student__name__icontains=filters['student_name']
            )

        # Status filters
        if 'status' in filters:
            status = filters['status']
            if status == 'checked_in':
                queryset = queryset.filter(
                    check_in_time__isnull=False,
                    check_out_time__isnull=True
                )
            elif status == 'checked_out':
                queryset = queryset.filter(check_out_time__isnull=False)
            elif status == 'absent':
                queryset = queryset.filter(check_in_time__isnull=True)

        # Department filter
        if 'department' in filters:
            queryset = queryset.filter(
                student__student_class__icontains=filters['department']
            )

        # Minimum duration
        if 'min_duration_hours' in filters:
            min_duration = int(filters['min_duration_hours']) * 3600
            from django.db.models import F, ExpressionWrapper, DurationField
            from datetime import timedelta
            
            queryset = queryset.filter(
                check_in_time__isnull=False,
                check_out_time__isnull=False
            ).annotate(
                duration_seconds=ExpressionWrapper(
                    F('check_out_time') - F('check_in_time'),
                    output_field=DurationField()
                )
            ).filter(duration_seconds__gte=timedelta(seconds=min_duration))

        return queryset.order_by('-date', '-check_in_time')

    @staticmethod
    def export_attendance_to_csv(queryset, filename='attendance.csv'):
        """Export attendance records to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Student ID', 'Name', 'Email', 'Department', 'Date',
            'Check In', 'Check Out', 'Duration', 'Status'
        ])

        for record in queryset:
            duration = record.calculate_duration() if record.check_out_time else 'N/A'
            status = 'Present' if record.check_in_time else 'Absent'

            writer.writerow([
                record.student.id,
                record.student.name,
                record.student.email,
                record.student.student_class,
                record.date.isoformat(),
                record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '',
                record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else '',
                duration,
                status
            ])

        logger.info(f"Exported {queryset.count()} attendance records to CSV")
        return response

    @staticmethod
    def export_students_to_csv(queryset, filename='students.csv'):
        """Export students to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Student ID', 'Name', 'Email', 'Phone', 'Department',
            'Authorized', 'Face Recognized', 'Created Date'
        ])

        for student in queryset:
            writer.writerow([
                student.id,
                student.name,
                student.email,
                student.phone_number,
                student.student_class,
                'Yes' if student.authorized else'No',
                'Yes' if student.face_recognized else 'No',
                student.created_at.date().isoformat() if student.created_at else ''
            ])

        logger.info(f"Exported {queryset.count()} students to CSV")
        return response

    @staticmethod
    def export_analytics_report_to_csv(analytics_data, filename='report.csv'):
        """Export analytics report to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # Write header
        writer.writerow(['Attendance Analytics Report'])
        writer.writerow(['Report Generated:', date.today().isoformat()])
        writer.writerow([])

        # Write summary
        writer.writerow(['Overall Summary'])
        summary = analytics_data.get('overall_metrics', {}).get('summary', {})
        for key, value in summary.items():
            writer.writerow([key.replace('_', ' ').title(), value])

        writer.writerow([])
        writer.writerow([])

        # Write department statistics
        writer.writerow(['Department Statistics'])
        writer.writerow([
            'Department', 'Total Students', 'Expected Attendance',
            'Actual Attendance', 'Attendance Rate', 'Authorized'
        ])

        for dept in analytics_data.get('department_statistics', []):
            writer.writerow([
                dept['department'],
                dept['total_students'],
                dept['expected_attendance'],
                dept['actual_attendance'],
                f"{dept['attendance_rate']}%",
                dept['authorized']
            ])

        logger.info("Exported analytics report to CSV")
        return response

    @staticmethod
    def get_advanced_search_suggestions(query, search_type='student'):
        """Get search suggestions for autocomplete"""
        query_lower = query.lower()

        if search_type == 'student':
            suggestions = Student.objects.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query)
            ).values('id', 'name', 'email')[:10]

        elif search_type == 'department':
            suggestions = Student.objects\
                .filter(student_class__icontains=query)\
                .values_list('student_class', flat=True)\
                .distinct()[:10]

        else:
            suggestions = []

        return list(suggestions)
