"""
Advanced analytics and reporting dashboard
Provides comprehensive attendance analytics and insights
"""

from django.db.models import Count, Q, F, Sum, Avg
from django.utils import timezone
from datetime import date, timedelta, datetime
from app1.models import Student, Attendance
import json
import logging

logger = logging.getLogger(__name__)


class AttendanceAnalytics:
    """Core analytics for attendance data"""

    @staticmethod
    def get_daily_statistics(target_date=None):
        """Get daily attendance statistics"""
        if not target_date:
            target_date = date.today()

        records = Attendance.objects.filter(date=target_date)

        return {
            'date': target_date.isoformat(),
            'total_records': records.count(),
            'present': records.filter(status='Present').count(),
            'absent': records.filter(status='Absent').count(),
            'late': records.filter(status='Late').count(),
            'leave': records.filter(status='Leave').count(),
            'attendance_rate': round(
                (records.filter(status='Present').count() / 
                 max(records.count(), 1) * 100), 2
            ),
            'timestamp': datetime.now().isoformat(),
        }

    @staticmethod
    def get_weekly_statistics(weeks_back=0):
        """Get weekly attendance statistics"""
        today = date.today()
        monday = today - timedelta(days=today.weekday() + (7 * weeks_back))
        sunday = monday + timedelta(days=6)

        records = Attendance.objects.filter(
            date__gte=monday,
            date__lte=sunday
        )

        daily_breakdown = {}
        for i in range(7):
            day = monday + timedelta(days=i)
            day_records = records.filter(date=day)
            daily_breakdown[day.strftime('%A')] = {
                'date': day.isoformat(),
                'present': day_records.filter(status='Present').count(),
                'absent': day_records.filter(status='Absent').count(),
                'late': day_records.filter(status='Late').count(),
            }

        return {
            'week_start': monday.isoformat(),
            'week_end': sunday.isoformat(),
            'total_records': records.count(),
            'present': records.filter(status='Present').count(),
            'absent': records.filter(status='Absent').count(),
            'late': records.filter(status='Late').count(),
            'daily_breakdown': daily_breakdown,
            'average_daily_attendance': round(
                records.count() / max(7, 1), 2
            ),
        }

    @staticmethod
    def get_monthly_statistics(year=None, month=None):
        """Get monthly attendance statistics"""
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month

        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        records = Attendance.objects.filter(
            date__gte=month_start,
            date__lte=month_end
        )

        return {
            'year': year,
            'month': month,
            'month_name': month_start.strftime('%B'),
            'total_records': records.count(),
            'present': records.filter(status='Present').count(),
            'absent': records.filter(status='Absent').count(),
            'late': records.filter(status='Late').count(),
            'unique_students': records.values('student').distinct().count(),
            'attendance_rate': round(
                (records.filter(status='Present').count() / 
                 max(records.count(), 1) * 100), 2
            ),
        }

    @staticmethod
    def get_student_analytics(student_id, days=30):
        """Get detailed analytics for a student"""
        student = Student.objects.get(id=student_id)
        start_date = date.today() - timedelta(days=days)

        records = Attendance.objects.filter(
            student=student,
            date__gte=start_date
        )

        return {
            'student': {
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'class': student.student_class,
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': date.today().isoformat(),
                'days': days,
            },
            'statistics': {
                'total_records': records.count(),
                'present': records.filter(status='Present').count(),
                'absent': records.filter(status='Absent').count(),
                'late': records.filter(status='Late').count(),
                'attendance_percentage': round(
                    (records.filter(status='Present').count() / 
                     max(records.count(), 1) * 100), 2
                ),
            },
            'trends': {
                'week_1': AttendanceAnalytics._get_period_stats(records, 0, 7),
                'week_2': AttendanceAnalytics._get_period_stats(records, 7, 14),
                'week_3': AttendanceAnalytics._get_period_stats(records, 14, 21),
                'week_4': AttendanceAnalytics._get_period_stats(records, 21, 30),
            }
        }

    @staticmethod
    def _get_period_stats(records, start_days, end_days):
        """Get statistics for a period"""
        start_date = date.today() - timedelta(days=end_days)
        end_date = date.today() - timedelta(days=start_days)

        period_records = records.filter(date__gte=start_date, date__lte=end_date)

        return {
            'total': period_records.count(),
            'present': period_records.filter(status='Present').count(),
            'absent': period_records.filter(status='Absent').count(),
            'late': period_records.filter(status='Late').count(),
        }


class ClassAnalytics:
    """Analytics for classes and departments"""

    @staticmethod
    def get_class_statistics(class_name, date_filter=None):
        """Get statistics for a class"""
        students = Student.objects.filter(student_class__icontains=class_name)
        student_ids = list(students.values_list('id', flat=True))

        queryset = Attendance.objects.filter(student_id__in=student_ids)
        if date_filter:
            queryset = queryset.filter(date=date_filter)

        return {
            'class': class_name,
            'total_students': students.count(),
            'authorized_students': students.filter(authorized=True).count(),
            'statistics': {
                'total_records': queryset.count(),
                'present': queryset.filter(status='Present').count(),
                'absent': queryset.filter(status='Absent').count(),
                'late': queryset.filter(status='Late').count(),
                'attendance_rate': round(
                    (queryset.filter(status='Present').count() / 
                     max(queryset.count(), 1) * 100), 2
                ),
            },
            'average_attendance_per_student': round(
                queryset.count() / max(students.count(), 1), 2
            ),
        }

    @staticmethod
    def get_class_comparison(date_range_days=30):
        """Compare attendance across all classes"""
        today = date.today()
        start_date = today - timedelta(days=date_range_days)

        classes = Student.objects.values('student_class').distinct()
        comparison = []

        for class_obj in classes:
            class_name = class_obj['student_class']
            students = Student.objects.filter(student_class=class_name)
            student_ids = list(students.values_list('id', flat=True))

            records = Attendance.objects.filter(
                student_id__in=student_ids,
                date__gte=start_date
            )

            comparison.append({
                'class': class_name,
                'total_students': students.count(),
                'total_records': records.count(),
                'present': records.filter(status='Present').count(),
                'absent': records.filter(status='Absent').count(),
                'late': records.filter(status='Late').count(),
                'attendance_rate': round(
                    (records.filter(status='Present').count() / 
                     max(records.count(), 1) * 100), 2
                ),
            })

        return {
            'comparison_period': f"Last {date_range_days} days",
            'classes': sorted(comparison, key=lambda x: x['attendance_rate'], reverse=True),
        }

    @staticmethod
    def get_at_risk_students(class_name=None, threshold=75):
        """Get students below attendance threshold"""
        students = Student.objects.all()
        if class_name:
            students = students.filter(student_class__icontains=class_name)

        at_risk = []

        for student in students:
            records = Attendance.objects.filter(student=student)
            if records.count() > 0:
                percent = (records.filter(status='Present').count() / 
                          records.count() * 100)
                if percent < threshold:
                    at_risk.append({
                        'student_id': student.id,
                        'name': student.name,
                        'roll_number': student.roll_number,
                        'class': student.student_class,
                        'attendance_percentage': round(percent, 2),
                        'present_days': records.filter(status='Present').count(),
                        'total_days': records.count(),
                        'risk_level': 'critical' if percent < 50 else 'warning',
                    })

        return {
            'threshold': threshold,
            'at_risk_count': len(at_risk),
            'students': sorted(at_risk, key=lambda x: x['attendance_percentage']),
        }


class TrendAnalysis:
    """Analyze trends in attendance data"""

    @staticmethod
    def get_attendance_trend(days=90):
        """Get attendance trend over time"""
        start_date = date.today() - timedelta(days=days)
        trend = {}

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            records = Attendance.objects.filter(date=current_date)

            trend[current_date.isoformat()] = {
                'date': current_date.isoformat(),
                'day': current_date.strftime('%A'),
                'total': records.count(),
                'present': records.filter(status='Present').count(),
                'absent': records.filter(status='Absent').count(),
                'late': records.filter(status='Late').count(),
                'rate': round(
                    (records.filter(status='Present').count() / 
                     max(records.count(), 1) * 100), 2
                ) if records.count() > 0 else 0,
            }

        return {
            'period': f"Last {days} days",
            'start_date': start_date.isoformat(),
            'end_date': date.today().isoformat(),
            'data': trend,
        }

    @staticmethod
    def get_day_of_week_analysis():
        """Analyze attendance by day of week"""
        days_analysis = {
            'Monday': [],
            'Tuesday': [],
            'Wednesday': [],
            'Thursday': [],
            'Friday': [],
            'Saturday': [],
            'Sunday': [],
        }

        all_records = Attendance.objects.all()

        for record in all_records:
            day_name = record.date.strftime('%A')
            if day_name in days_analysis:
                days_analysis[day_name].append({
                    'status': record.status,
                    'date': record.date.isoformat(),
                })

        summary = {}
        for day, records in days_analysis.items():
            if records:
                summary[day] = {
                    'total': len(records),
                    'present': sum(1 for r in records if r['status'] == 'Present'),
                    'absent': sum(1 for r in records if r['status'] == 'Absent'),
                    'late': sum(1 for r in records if r['status'] == 'Late'),
                    'rate': round(
                        sum(1 for r in records if r['status'] == 'Present') / 
                        len(records) * 100, 2
                    ),
                }

        return summary

    @staticmethod
    def get_time_series_data(granularity='daily', days=30):
        """Get time series data for charts"""
        start_date = date.today() - timedelta(days=days)
        data_points = []

        if granularity == 'daily':
            for i in range(days):
                current_date = start_date + timedelta(days=i)
                records = Attendance.objects.filter(date=current_date)

                data_points.append({
                    'timestamp': current_date.isoformat(),
                    'present': records.filter(status='Present').count(),
                    'absent': records.filter(status='Absent').count(),
                    'late': records.filter(status='Late').count(),
                    'total': records.count(),
                })

        return {
            'granularity': granularity,
            'period_days': days,
            'data': data_points,
        }


class DashboardGenerator:
    """Generate complete dashboard data"""

    @staticmethod
    def get_executive_dashboard():
        """Get high-level executive dashboard"""
        today = date.today()

        return {
            'generated_at': datetime.now().isoformat(),
            'today': AttendanceAnalytics.get_daily_statistics(today),
            'week': AttendanceAnalytics.get_weekly_statistics(),
            'month': AttendanceAnalytics.get_monthly_statistics(),
            'total_students': Student.objects.count(),
            'authorized_students': Student.objects.filter(authorized=True).count(),
            'class_comparison': ClassAnalytics.get_class_comparison(),
            'at_risk_students': ClassAnalytics.get_at_risk_students(),
            'trends': TrendAnalysis.get_attendance_trend(days=30),
        }

    @staticmethod
    def get_teacher_dashboard(class_name):
        """Get teacher-specific dashboard for their class"""
        return {
            'generated_at': datetime.now().isoformat(),
            'class': class_name,
            'today': ClassAnalytics.get_class_statistics(class_name, date.today()),
            'week': AttendanceAnalytics.get_weekly_statistics(),
            'at_risk_students': ClassAnalytics.get_at_risk_students(
                class_name=class_name,
                threshold=75
            ),
            'day_analysis': TrendAnalysis.get_day_of_week_analysis(),
        }

    @staticmethod
    def get_student_dashboard(student_id):
        """Get student-specific dashboard"""
        student = Student.objects.get(id=student_id)

        return {
            'generated_at': datetime.now().isoformat(),
            'student': {
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'class': student.student_class,
            },
            'analytics_30_days': AttendanceAnalytics.get_student_analytics(student_id, 30),
            'analytics_90_days': AttendanceAnalytics.get_student_analytics(student_id, 90),
            'today': AttendanceAnalytics.get_daily_statistics(),
        }
