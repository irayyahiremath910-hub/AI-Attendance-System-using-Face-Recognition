"""
Email notification system for attendance and student status updates
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from app1.models import Student, Attendance
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""
    
    FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
    
    @staticmethod
    def send_attendance_reminder(student):
        """Send attendance reminder email to student"""
        try:
            subject = f'Attendance Reminder - {student.name}'
            
            context = {
                'student_name': student.name,
                'student_email': student.email,
                'date': date.today().strftime('%Y-%m-%d'),
                'site_name': 'AI Attendance System'
            }
            
            # Plain text version
            text_content = f"""
Hello {student.name},

This is a reminder to mark your attendance for today ({date.today().strftime('%Y-%m-%d')}).

Please check in when you arrive at the facility.

Best regards,
AI Attendance System
"""
            
            html_content = f"""
<html>
    <body>
        <h3>Attendance Reminder</h3>
        <p>Hello {student.name},</p>
        <p>This is a reminder to mark your attendance for today (<strong>{date.today().strftime('%Y-%m-%d')}</strong>).</p>
        <p>Please check in when you arrive at the facility.</p>
        <hr>
        <p><em>AI Attendance System</em></p>
    </body>
</html>
"""
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=EmailNotificationService.FROM_EMAIL,
                to=[student.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Attendance reminder sent to {student.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send attendance reminder: {str(e)}")
            return False
    
    @staticmethod
    def send_check_in_confirmation(student):
        """Send check-in confirmation email"""
        try:
            subject = f'Check-In Confirmed - {date.today().strftime("%Y-%m-%d")}'
            
            text_content = f"""
Hello {student.name},

Your check-in has been successfully recorded for today.

Date: {date.today().strftime('%Y-%m-%d')}
Status: Checked In

Best regards,
AI Attendance System
"""
            
            html_content = f"""
<html>
    <body>
        <h3>✓ Check-In Confirmed</h3>
        <p>Hello {student.name},</p>
        <p>Your check-in has been <strong>successfully recorded</strong> for today.</p>
        <ul>
            <li><strong>Date:</strong> {date.today().strftime('%Y-%m-%d')}</li>
            <li><strong>Status:</strong> Checked In</li>
        </ul>
        <hr>
        <p><em>AI Attendance System</em></p>
    </body>
</html>
"""
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=EmailNotificationService.FROM_EMAIL,
                to=[student.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Check-in confirmation sent to {student.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send check-in confirmation: {str(e)}")
            return False
    
    @staticmethod
    def send_attendance_report(student, days=7):
        """Send weekly attendance report"""
        try:
            from django.db.models import Q
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            records = Attendance.objects.filter(
                student=student,
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            attended_count = records.filter(check_in_time__isnull=False).count()
            total_days = (end_date - start_date).days + 1
            attendance_rate = round((attended_count / total_days * 100) if total_days > 0 else 0, 2)
            
            subject = f'Weekly Attendance Report - {student.name}'
            
            attendance_details = '\n'.join([
                f"  {r.date}: {'✓ Present' if r.check_in_time else '✗ Absent'}"
                for r in records
            ])
            
            text_content = f"""
Hello {student.name},

Here is your attendance report for the week of {start_date} to {end_date}.

Summary:
--------
Days Attended: {attended_count}/{total_days}
Attendance Rate: {attendance_rate}%

Details:
{attendance_details}

Best regards,
AI Attendance System
"""
            
            html_content = f"""
<html>
    <body>
        <h3>Weekly Attendance Report</h3>
        <p>Hello {student.name},</p>
        <p>Here is your attendance report for the week of <strong>{start_date} to {end_date}</strong>.</p>
        
        <h4>Summary</h4>
        <ul>
            <li><strong>Days Attended:</strong> {attended_count}/{total_days}</li>
            <li><strong>Attendance Rate:</strong> {attendance_rate}%</li>
        </ul>
        
        <h4>Details</h4>
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f0f0f0;">
                <th style="border: 1px solid #ddd; padding: 8px;">Date</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Status</th>
            </tr>
"""
            
            for record in records:
                status = '✓ Present' if record.check_in_time else '✗ Absent'
                html_content += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{record.date}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{status}</td>
            </tr>
"""
            
            html_content += """
        </table>
        <hr>
        <p><em>AI Attendance System</em></p>
    </body>
</html>
"""
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=EmailNotificationService.FROM_EMAIL,
                to=[student.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Attendance report sent to {student.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send attendance report: {str(e)}")
            return False
    
    @staticmethod
    def send_student_authorization_notification(student):
        """Send notification when student is authorized"""
        try:
            subject = 'Account Authorized - Ready for Attendance'
            
            text_content = f"""
Hello {student.name},

Great news! Your account has been authorized for face recognition-based attendance.

Your face has been successfully encoded and you are now ready to use the attendance system.

To check in:
1. Approach the camera
2. Your face will be recognized automatically
3. Your attendance will be recorded

If you have any issues, please contact the administrator.

Best regards,
AI Attendance System
"""
            
            html_content = f"""
<html>
    <body>
        <h3>✓ Account Authorized</h3>
        <p>Hello {student.name},</p>
        <p>Great news! Your account has been <strong>authorized for face recognition-based attendance</strong>.</p>
        
        <p>Your face has been successfully encoded and you are now ready to use the attendance system.</p>
        
        <h4>How to Check In:</h4>
        <ol>
            <li>Approach the camera</li>
            <li>Your face will be recognized automatically</li>
            <li>Your attendance will be recorded</li>
        </ol>
        
        <p>If you have any issues, please contact the administrator.</p>
        <hr>
        <p><em>AI Attendance System</em></p>
    </body>
</html>
"""
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=EmailNotificationService.FROM_EMAIL,
                to=[student.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Authorization notification sent to {student.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send authorization notification: {str(e)}")
            return False
