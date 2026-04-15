"""
Attendance Analytics Service
Provides comprehensive analytics, metrics, and reporting for attendance data
"""

from app1.models import Student, Attendance
from django.utils import timezone
from django.db.models import Q, Count, F, Case, When, DecimalField, Avg
from datetime import date, timedelta, datetime
import logging

logger = logging.getLogger(__name__)


class AttendanceAnalyticsService:
    """Service for attendance analytics and statistics"""

    @staticmethod
    def get_attendance_metrics(start_date=None, end_date=None):
        """Get comprehensive attendance metrics"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        records = Attendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        total_records = records.count()
        checked_in = records.filter(check_in_time__isnull=False).count()
        checked_out = records.filter(check_out_time__isnull=False).count()
        present = records.filter(check_in_time__isnull=False, check_out_time__isnull=False).count()
        absent = Student.objects.count() * (end_date - start_date).days - total_records

        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days + 1
            },
            'summary': {
                'total_records': total_records,
                'checked_in': checked_in,
                'checked_out': checked_out,
                'present': present,
                'absent': max(0, absent),
                'presence_rate': round((checked_in / total_records * 100) if total_records > 0 else 0, 2)
            }
        }

    @staticmethod
    def get_student_attendance_metrics(student, days=30):
        """Get metrics for individual student"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        records = Attendance.objects.filter(
            student=student,
            date__gte=start_date,
            date__lte=end_date
        )

        present = records.filter(check_in_time__isnull=False).count()
        absent = (end_date - start_date).days + 1 - present

        # Calculate average duration
        durations = []
        for record in records.filter(check_in_time__isnull=False, check_out_time__isnull=False):
            duration = (record.check_out_time - record.check_in_time).total_seconds() / 3600
            durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            'student_id': student.id,
            'student_name': student.name,
            'period_days': (end_date - start_date).days + 1,
            'present': present,
            'absent': absent,
            'attendance_rate': round((present / ((end_date - start_date).days + 1) * 100), 2),
            'average_duration_hours': round(avg_duration, 2),
            'total_hours': round(sum(durations), 2)
        }

    @staticmethod
    def get_department_statistics(start_date=None, end_date=None):
        """Get statistics by department"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        departments = Student.objects.values('student_class').distinct()
        stats = []

        for dept in departments:
            dept_name = dept['student_class']
            dept_students = Student.objects.filter(student_class=dept_name)
            total_students = dept_students.count()

            records = Attendance.objects.filter(
                student__in=dept_students,
                date__gte=start_date,
                date__lte=end_date
            )

            present = records.filter(check_in_time__isnull=False).count()
            expected = total_students * ((end_date - start_date).days + 1)

            stats.append({
                'department': dept_name,
                'total_students': total_students,
                'expected_attendance': expected,
                'actual_attendance': present,
                'attendance_rate': round((present / expected * 100) if expected > 0 else 0, 2),
                'authorized': dept_students.filter(authorized=True).count(),
                'face_recognized': dept_students.filter(face_recognized=True).count()
            })

        return sorted(stats, key=lambda x: x['attendance_rate'], reverse=True)

    @staticmethod
    def get_daily_trends(days=30):
        """Get daily attendance trends"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        trends = []
        current_date = start_date

        while current_date <= end_date:
            records = Attendance.objects.filter(
                date=current_date,
                check_in_time__isnull=False
            )

            total_students = Student.objects.count()
            present = records.count()

            trends.append({
                'date': current_date.isoformat(),
                'present': present,
                'absent': total_students - present,
                'attendance_rate': round((present / total_students * 100) if total_students > 0 else 0, 2)
            })

            current_date += timedelta(days=1)

        return trends

    @staticmethod
    def get_peak_hours(start_date=None, end_date=None):
        """Get peak check-in times"""
        if not start_date:
            start_date = date.today() - timedelta(days=7)
        if not end_date:
            end_date = date.today()

        records = Attendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            check_in_time__isnull=False
        )

        # Group by hour
        peak_hours = {}
        for record in records:
            hour = record.check_in_time.hour
            peak_hours[hour] = peak_hours.get(hour, 0) + 1

        sorted_hours = sorted(peak_hours.items(), key=lambda x: x[1], reverse=True)

        return [
            {'hour': f'{hour:02d}:00', 'count': count}
            for hour, count in sorted_hours[:10]
        ]

    @staticmethod
    def get_attendance_summary_report(start_date=None, end_date=None):
        """Generate comprehensive attendance summary report"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        return {
            'report_date': date.today().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'overall_metrics': AttendanceAnalyticsService.get_attendance_metrics(start_date, end_date),
            'department_statistics': AttendanceAnalyticsService.get_department_statistics(start_date, end_date),
            'daily_trends': AttendanceAnalyticsService.get_daily_trends((end_date - start_date).days),
            'peak_hours': AttendanceAnalyticsService.get_peak_hours(start_date, end_date)
        }

    @staticmethod
    def get_attendance_forecast():
        """Predict attendance for next 7 days based on patterns"""
        # Simple forecast based on historical average
        historical_avg = Attendance.objects\
            .filter(date__gte=date.today() - timedelta(days=30))\
            .values('date')\
            .annotate(count=Count('id'))\
            .aggregate(avg=Avg('count'))['avg'] or 0

        forecast = []
        for i in range(1, 8):
            future_date = date.today() + timedelta(days=i)
            forecast.append({
                'date': future_date.isoformat(),
                'predicted_attendance': round(historical_avg),
                'confidence': 0.75
            })

        return forecast

    @staticmethod
    def identify_low_attendance_students(threshold=70, days=30):
        """Identify students with low attendance rate"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        students = Student.objects.all()
        low_attendance = []

        for student in students:
            metrics = AttendanceAnalyticsService.get_student_attendance_metrics(student, days)
            if metrics['attendance_rate'] < threshold:
                low_attendance.append(metrics)

        return sorted(low_attendance, key=lambda x: x['attendance_rate'])

    @staticmethod
    def get_system_health_metrics():
        """Get overall system health metrics"""
        total_students = Student.objects.count()
        authorized_students = Student.objects.filter(authorized=True).count()
        with_face_recognition = Student.objects.filter(face_recognized=True).count()

        today_attendance = Attendance.objects.filter(date=date.today())
        today_present = today_attendance.filter(check_in_time__isnull=False).count()

        return {
            'system_status': 'healthy',
            'total_students': total_students,
            'authorized': authorized_students,
            'authorization_rate': round((authorized_students / total_students * 100) if total_students > 0 else 0, 2),
            'with_face_recognition': with_face_recognition,
            'face_recognition_rate': round((with_face_recognition / total_students * 100) if total_students > 0 else 0, 2),
            'today_attendance_rate': round((today_present / total_students * 100) if total_students > 0 else 0, 2),
            'database_records': Attendance.objects.count()
        }
