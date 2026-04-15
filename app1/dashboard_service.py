"""
Admin Dashboard Service - Real-time monitoring and system management
"""

from app1.models import Student, Attendance
from datetime import date, timedelta, datetime
from django.db.models import Count, Q, Avg
from app1.analytics_service import AttendanceAnalyticsService
import logging

logger = logging.getLogger(__name__)


class AdminDashboardService:
    """Service for admin dashboard and real-time monitoring"""

    @staticmethod
    def get_dashboard_overview():
        """Get main dashboard overview with all key metrics"""
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Today's metrics
        today_attendance = Attendance.objects.filter(date=today)
        today_present = today_attendance.filter(check_in_time__isnull=False).count()
        today_absent = Student.objects.count() - today_present

        # This week
        week_records = Attendance.objects.filter(
            date__gte=week_ago,
            date__lte=today
        )
        week_present = week_records.filter(check_in_time__isnull=False).count()
        week_absent = week_records.filter(check_in_time__isnull=True).count()

        # This month
        month_records = Attendance.objects.filter(
            date__gte=month_ago,
            date__lte=today
        )
        month_present = month_records.filter(check_in_time__isnull=False).count()

        total_students = Student.objects.count()

        return {
            'timestamp': datetime.now().isoformat(),
            'today': {
                'date': today.isoformat(),
                'total_students': total_students,
                'present': today_present,
                'absent': today_absent,
                'attendance_rate': round((today_present / total_students * 100) if total_students > 0 else 0, 2),
                'checked_in_percentage': round((today_present / total_students * 100) if total_students > 0 else 0, 2)
            },
            'this_week': {
                'total_days': 7,
                'total_expected': total_students * 7,
                'present': week_present,
                'absent': week_absent,
                'attendance_rate': round((week_present / (total_students * 7) * 100) if total_students > 0 else 0, 2)
            },
            'this_month': {
                'total_days': (today - month_ago).days + 1,
                'present': month_present,
                'attendance_rate': round((month_present / (total_students * (today - month_ago).days) * 100) if total_students > 0 else 0, 2)
            },
            'system_health': AttendanceAnalyticsService.get_system_health_metrics()
        }

    @staticmethod
    def get_active_sessions():
        """Get currently active check-ins (without check-out)"""
        active = Attendance.objects.filter(
            date=date.today(),
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).select_related('student').order_by('-check_in_time')

        return [{
            'student_id': record.student.id,
            'student_name': record.student.name,
            'student_email': record.student.email,
            'department': record.student.student_class,
            'check_in_time': record.check_in_time.isoformat(),
            'duration_minutes': round((datetime.now().replace(tzinfo=record.check_in_time.tzinfo) - record.check_in_time).total_seconds() / 60)
        } for record in active]

    @staticmethod
    def get_recent_activities(limit=20):
        """Get recent attendance activities"""
        recent = Attendance.objects.filter(
            date=date.today()
        ).select_related('student').order_by('-check_in_time')[:limit]

        activities = []
        for record in recent:
            activity_type = 'Check Out' if record.check_out_time else 'Check In'
            timestamp = record.check_out_time if record.check_out_time else record.check_in_time

            activities.append({
                'activity': activity_type,
                'student': record.student.name,
                'department': record.student.student_class,
                'timestamp': timestamp.isoformat() if timestamp else None,
                'status': 'success'
            })

        return activities

    @staticmethod
    def get_pending_actions():
        """Get pending admin actions"""
        pending_actions = []

        # Students not authorized
        unauthorized = Student.objects.filter(authorized=False).count()
        if unauthorized > 0:
            pending_actions.append({
                'type': 'authorization',
                'title': f'{unauthorized} students need authorization',
                'priority': 'high',
                'action': 'bulk_authorize_students',
                'count': unauthorized
            })

        # Students without face encoding
        no_face = Student.objects.filter(face_recognized=False).count()
        if no_face > 0:
            pending_actions.append({
                'type': 'face_enrollment',
                'title': f'{no_face} students without face encoding',
                'priority': 'high',
                'action': 'enroll_faces',
                'count': no_face
            })

        # Unauthorized students and authorized count
        authorized = Student.objects.filter(authorized=True).count()
        if authorized > 0:
            pending_actions.append({
                'type': 'authorization_status',
                'title': f'{authorized} students authorized, ready for attendance',
                'priority': 'info',
                'status': 'completed',
                'count': authorized
            })

        # Low attendance alerts
        low_attendance = AttendanceAnalyticsService.identify_low_attendance_students(70, 30)
        if low_attendance:
            pending_actions.append({
                'type': 'low_attendance',
                'title': f'{len(low_attendance)} students with low attendance (<70%)',
                'priority': 'medium',
                'action': 'send_reminders',
                'count': len(low_attendance)
            })

        return sorted(pending_actions, key=lambda x: {'high': 0, 'medium': 1, 'low': 2, 'info': 3}.get(x.get('priority', 'info'), 3))

    @staticmethod
    def get_key_performance_indicators():
        """Get KPIs for dashboard"""
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        total_students = Student.objects.count()
        
        # Attendance trend
        today_rate = Attendance.objects\
            .filter(date=today, check_in_time__isnull=False)\
            .count() / total_students * 100 if total_students > 0 else 0
        
        week_rate = Attendance.objects\
            .filter(date__gte=week_ago, date__lte=today, check_in_time__isnull=False)\
            .count() / (total_students * 7) * 100 if total_students > 0 else 0

        # Authorization rate
        auth_rate = Student.objects.filter(authorized=True).count() / total_students * 100 if total_students > 0 else 0

        # Face recognition rate
        face_rate = Student.objects.filter(face_recognized=True).count() / total_students * 100 if total_students > 0 else 0

        return {
            'kpi': [
                {
                    'name': 'Today\'s Attendance Rate',
                    'value': round(today_rate, 2),
                    'unit': '%',
                    'trend': 'stable'
                },
                {
                    'name': 'Weekly Avg Attendance',
                    'value': round(week_rate, 2),
                    'unit': '%',
                    'trend': 'up' if week_rate > today_rate else 'down'
                },
                {
                    'name': 'Authorization Rate',
                    'value': round(auth_rate, 2),
                    'unit': '%',
                    'trend': 'stable'
                },
                {
                    'name': 'Face Recognition Rate',
                    'value': round(face_rate, 2),
                    'unit': '%',
                    'trend': 'up'
                },
                {
                    'name': 'Total Students',
                    'value': total_students,
                    'unit': 'count',
                    'trend': 'stable'
                },
                {
                    'name': 'Total Records',
                    'value': Attendance.objects.count(),
                    'unit': 'count',
                    'trend': 'up'
                }
            ]
        }

    @staticmethod
    def get_admin_alerts():
        """Get critical alerts for admin"""
        alerts = []

        # Check for no attendance today
        today_attendance = Attendance.objects.filter(date=date.today()).exists()
        if not today_attendance:
            alerts.append({
                'type': 'warning',
                'message': 'No attendance records for today',
                'severity': 'medium'
            })

        # Check for many absences
        total = Student.objects.count()
        today_absent = total - Attendance.objects.filter(
            date=date.today(),
            check_in_time__isnull=False
        ).count()

        if total > 0 and today_absent / total > 0.5:
            alerts.append({
                'type': 'alert',
                'message': f'High absence rate: {round(today_absent/total*100, 2)}% of students absent',
                'severity': 'high'
            })

        # Check for unauthorized students
        unauthorized = Student.objects.filter(authorized=False).count()
        if unauthorized > 0:
            alerts.append({
                'type': 'info',
                'message': f'{unauthorized} students still need authorization',
                'severity': 'low'
            })

        return alerts
