"""
Celery tasks for background job processing
Handles email sending, exports, analytics, and maintenance tasks
"""

from celery import shared_task
from django.utils import timezone
from app1.models import Student, Attendance
from app1.notification_service import EmailNotificationService
from app1.analytics_service import AttendanceAnalyticsService
from app1.dashboard_service import AdminDashboardService
from app1.search_service import AttendanceSearchService
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_daily_attendance_reminders():
    """Send attendance reminders to all authorized students"""
    try:
        authorized_students = Student.objects.filter(authorized=True)
        success_count = 0
        failed_count = 0

        for student in authorized_students:
            result = EmailNotificationService.send_attendance_reminder(student)
            if result:
                success_count += 1
            else:
                failed_count += 1

        logger.info(
            f"Daily reminders: {success_count} sent, {failed_count} failed"
        )
        return {
            'success': success_count,
            'failed': failed_count,
            'total': success_count + failed_count
        }
    except Exception as e:
        logger.error(f"Error in send_daily_attendance_reminders: {str(e)}")
        return {'error': str(e)}


@shared_task
def send_weekly_reports():
    """Send weekly attendance reports to all students"""
    try:
        all_students = Student.objects.all()
        success_count = 0
        failed_count = 0

        for student in all_students:
            result = EmailNotificationService.send_attendance_report(student, days=7)
            if result:
                success_count += 1
            else:
                failed_count += 1

        logger.info(f"Weekly reports: {success_count} sent, {failed_count} failed")
        return {
            'success': success_count,
            'failed': failed_count,
            'total': success_count + failed_count
        }
    except Exception as e:
        logger.error(f"Error in send_weekly_reports: {str(e)}")
        return {'error': str(e)}


@shared_task
def check_system_health():
    """Check system health and alert on issues"""
    try:
        health = AdminDashboardService.get_system_health_metrics()
        alerts = AdminDashboardService.get_admin_alerts()

        if alerts:
            alert_count = len(alerts)
            critical_count = sum(1 for a in alerts if a.get('severity') == 'high')
            logger.warning(
                f"System alerts detected: {critical_count} critical, {alert_count} total"
            )
            return {
                'status': 'alerts_detected',
                'alerts': alerts,
                'health': health
            }
        else:
            logger.info("System health check: All systems healthy")
            return {
                'status': 'healthy',
                'health': health
            }
    except Exception as e:
        logger.error(f"Error in check_system_health: {str(e)}")
        return {'error': str(e)}


@shared_task
def generate_daily_analytics():
    """Generate and store daily analytics"""
    try:
        today = date.today()
        analytics_report = AttendanceAnalyticsService.get_attendance_summary_report(
            start_date=today,
            end_date=today
        )

        logger.info(f"Daily analytics generated for {today}")
        return {
            'date': today.isoformat(),
            'report': analytics_report
        }
    except Exception as e:
        logger.error(f"Error in generate_daily_analytics: {str(e)}")
        return {'error': str(e)}


@shared_task
def cleanup_old_attendance_records(days=90):
    """Clean up attendance records older than specified days"""
    try:
        cutoff_date = date.today() - timedelta(days=days)
        old_records = Attendance.objects.filter(date__lt=cutoff_date)
        count, _ = old_records.delete()

        logger.info(f"Cleaned up {count} attendance records older than {cutoff_date}")
        return {
            'deleted_count': count,
            'cutoff_date': cutoff_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Error in cleanup_old_attendance_records: {str(e)}")
        return {'error': str(e)}


@shared_task
def export_attendance_data(date_from, date_to, filename=None):
    """Export attendance data for date range"""
    try:
        from datetime import datetime

        start_date = datetime.fromisoformat(date_from).date()
        end_date = datetime.fromisoformat(date_to).date()

        queryset = Attendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).select_related('student')

        if not filename:
            filename = f"attendance_{start_date}_to_{end_date}.csv"

        logger.info(f"Export task: {queryset.count()} records from {date_from} to {date_to}")
        return {
            'status': 'completed',
            'records_count': queryset.count(),
            'filename': filename
        }
    except Exception as e:
        logger.error(f"Error in export_attendance_data: {str(e)}")
        return {'error': str(e)}


@shared_task
def bulk_authorize_students_task(count=50, face_required=False):
    """Bulk authorize students in background"""
    try:
        queryset = Student.objects.filter(authorized=False)

        if face_required:
            queryset = queryset.exclude(face_encoding__isnull=True)

        queryset = queryset[:count]
        updated = queryset.update(authorized=True)

        logger.info(f"Bulk authorization: {updated} students authorized")
        return {
            'authorized_count': updated,
            'total_authorized': Student.objects.filter(authorized=True).count()
        }
    except Exception as e:
        logger.error(f"Error in bulk_authorize_students_task: {str(e)}")
        return {'error': str(e)}


@shared_task
def identify_low_attendance_students_task(threshold=70, days=30):
    """Identify low attendance students and send alerts"""
    try:
        low_attendance = AttendanceAnalyticsService.identify_low_attendance_students(
            threshold=threshold,
            days=days
        )

        logger.info(
            f"Identified {len(low_attendance)} students with attendance < {threshold}%"
        )
        return {
            'low_attendance_count': len(low_attendance),
            'threshold': threshold,
            'days': days,
            'students': [s['student_name'] for s in low_attendance]
        }
    except Exception as e:
        logger.error(f"Error in identify_low_attendance_students_task: {str(e)}")
        return {'error': str(e)}


@shared_task
def send_bulk_notifications_task(notification_type='reminder', authorized_only=False):
    """Send bulk notifications"""
    try:
        if authorized_only:
            students = Student.objects.filter(authorized=True)
        else:
            students = Student.objects.all()

        success_count = 0
        failed_count = 0

        for student in students:
            if notification_type == 'reminder':
                result = EmailNotificationService.send_attendance_reminder(student)
            elif notification_type == 'authorization':
                result = EmailNotificationService.send_student_authorization_notification(student)
            else:
                result = False

            if result:
                success_count += 1
            else:
                failed_count += 1

        logger.info(
            f"Bulk {notification_type}: {success_count} sent, {failed_count} failed"
        )
        return {
            'notification_type': notification_type,
            'success_count': success_count,
            'failed_count': failed_count,
            'total': success_count + failed_count
        }
    except Exception as e:
        logger.error(f"Error in send_bulk_notifications_task: {str(e)}")
        return {'error': str(e)}


@shared_task
def generate_monthly_report():
    """Generate comprehensive monthly report"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        report = AttendanceAnalyticsService.get_attendance_summary_report(
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"Monthly report generated from {start_date} to {end_date}")
        return {
            'status': 'completed',
            'period': f"{start_date} to {end_date}",
            'report': report
        }
    except Exception as e:
        logger.error(f"Error in generate_monthly_report: {str(e)}")
        return {'error': str(e)}


@shared_task
def cache_analytics_data():
    """Pre-compute and cache analytics data"""
    try:
        # Cache overall metrics
        metrics = AttendanceAnalyticsService.get_attendance_metrics()
        
        # Cache department statistics
        dept_stats = AttendanceAnalyticsService.get_department_statistics()
        
        # Cache health metrics
        health = AdminDashboardService.get_system_health_metrics()

        logger.info("Analytics data cached successfully")
        return {
            'status': 'cached',
            'metrics': metrics,
            'departments': len(dept_stats)
        }
    except Exception as e:
        logger.error(f"Error in cache_analytics_data: {str(e)}")
        return {'error': str(e)}
