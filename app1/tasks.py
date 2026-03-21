from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Student, Attendance, AttendanceAlert


@shared_task
def send_low_attendance_alerts():
    """Send email alerts for students with low attendance"""
    threshold = getattr(settings, 'MIN_ATTENDANCE_THRESHOLD', 75)
    
    students = Student.objects.filter(authorized=True)
    alerts_sent = 0
    
    for student in students:
        attendance_percentage = student.get_attendance_percentage()
        
        if attendance_percentage < threshold:
            # Check if alert already exists and not sent
            alert, created = AttendanceAlert.objects.get_or_create(
                student=student,
                alert_type='low_attendance',
                defaults={
                    'message': f'Your attendance ({attendance_percentage:.1f}%) is below the required threshold ({threshold}%)'
                }
            )
            
            if created and not alert.is_sent:
                send_attendance_alert_email.delay(alert.id)
                alerts_sent += 1
    
    return f"Created {alerts_sent} low attendance alerts"


@shared_task
def send_attendance_alert_email(alert_id):
    """Send email for an attendance alert"""
    try:
        alert = AttendanceAlert.objects.get(id=alert_id)
        
        subject = f"Attendance Alert: {alert.get_alert_type_display()}"
        message = f"""
        Dear {alert.student.name},
        
        {alert.message}
        
        Please ensure you maintain proper attendance to meet the minimum requirements.
        
        Best regards,
        Attendance System
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [alert.student.email],
            fail_silently=False,
        )
        
        alert.is_sent = True
        alert.sent_at = timezone.now()
        alert.save()
        
        return f"Alert email sent to {alert.student.email}"
    
    except AttendanceAlert.DoesNotExist:
        return "Alert not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def check_absent_students():
    """Check for students absent for more than a week and send alerts"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Get all authorized students
    all_students = Student.objects.filter(authorized=True).values_list('id', flat=True)
    
    # Get students present in the last 7 days
    present_students = Attendance.objects.filter(
        date__range=[week_ago, today],
        check_in_time__isnull=False
    ).values_list('student_id', flat=True).distinct()
    
    # Find students absent for a week
    absent_students = set(all_students) - set(present_students)
    
    alerts_created = 0
    for student_id in absent_students:
        student = Student.objects.get(id=student_id)
        alert, created = AttendanceAlert.objects.get_or_create(
            student=student,
            alert_type='absent_week',
            defaults={
                'message': f'You have been absent for 7 consecutive days. Please contact administration.'
            }
        )
        
        if created and not alert.is_sent:
            send_attendance_alert_email.delay(alert.id)
            alerts_created += 1
    
    return f"Created {alerts_created} one-week absence alerts"


@shared_task
def update_attendance_summary():
    """Update monthly attendance summaries"""
    from django.db.models import Q, Count
    from .models import AttendanceSummary
    
    today = timezone.now().date()
    current_month = today.strftime('%Y-%m')
    
    students = Student.objects.filter(authorized=True)
    updated = 0
    
    for student in students:
        # Count attendance for current month
        month_start = today.replace(day=1)
        month_attendance = Attendance.objects.filter(
            student=student,
            date__year=today.year,
            date__month=today.month
        )
        
        present_days = month_attendance.filter(check_in_time__isnull=False).count()
        absent_days = month_attendance.filter(check_in_time__isnull=True).count()
        late_days = month_attendance.filter(status='late').count()
        
        total_days = present_days + absent_days
        percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        summary, _ = AttendanceSummary.objects.update_or_create(
            student=student,
            month=current_month,
            defaults={
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'percentage': percentage
            }
        )
        updated += 1
    
    return f"Updated {updated} attendance summaries"


@shared_task
def send_weekly_report():
    """Send weekly attendance reports to admins"""
    from django.contrib.auth.models import User
    
    # Get all superusers
    admins = User.objects.filter(is_superuser=True)
    
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Get weekly statistics
    total_present = Attendance.objects.filter(
        date__range=[week_start, week_end],
        check_in_time__isnull=False
    ).count()
    
    total_absent = Attendance.objects.filter(
        date__range=[week_start, week_end],
        check_in_time__isnull=True
    ).count()
    
    for admin in admins:
        subject = f"Weekly Attendance Report - {week_start} to {week_end}"
        message = f"""
        Weekly Attendance Summary
        
        Week: {week_start} - {week_end}
        
        Total Students Marked Present: {total_present}
        Total Students Marked Absent: {total_absent}
        
        Please log in to the dashboard for detailed reports.
        
        Best regards,
        Attendance System
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin.email],
            fail_silently=True,
        )
    
    return f"Weekly reports sent to {admins.count()} admins"
