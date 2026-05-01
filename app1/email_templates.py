"""
Email and notification template system
Manages customizable email templates and notification messages
"""

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import date, timedelta
from app1.models import Student, Attendance
import logging

logger = logging.getLogger(__name__)


class EmailTemplate:
    """Base class for email templates"""

    subject = ""
    template_name = ""

    def __init__(self, recipient=None, context=None):
        self.recipient = recipient
        self.context = context or {}

    def get_subject(self):
        """Get email subject"""
        return self.subject

    def get_template_name(self):
        """Get template name"""
        return self.template_name

    def get_context(self):
        """Get template context"""
        return self.context

    def render_body(self):
        """Render HTML body"""
        try:
            return render_to_string(self.get_template_name(), self.get_context())
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            return None

    def send(self, from_email=None):
        """Send email"""
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        body = self.render_body()
        if not body:
            return False

        try:
            email = EmailMultiAlternatives(
                subject=self.get_subject(),
                body="",
                from_email=from_email,
                to=[self.recipient] if isinstance(self.recipient, str) else self.recipient
            )
            email.attach_alternative(body, "text/html")
            email.send()
            logger.info(f"Email sent to {self.recipient}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False


class AuthorizationTemplate(EmailTemplate):
    """Student authorization notification template"""

    subject = "Welcome to Attendance System - Account Authorized"
    template_name = "emails/authorization_notification.html"

    def get_context(self):
        context = super().get_context()
        if isinstance(self.recipient, Student):
            context.update({
                'student_name': self.recipient.name,
                'student_roll': self.recipient.roll_number,
                'student_class': self.recipient.student_class,
                'authorization_date': date.today(),
            })
        return context


class DailyReminderTemplate(EmailTemplate):
    """Daily attendance reminder template"""

    subject = "Daily Attendance Reminder"
    template_name = "emails/daily_reminder.html"

    def get_context(self):
        context = super().get_context()
        if isinstance(self.recipient, Student):
            # Get today's attendance status
            today_attendance = Attendance.objects.filter(
                student=self.recipient,
                date=date.today()
            ).first()

            context.update({
                'student_name': self.recipient.name,
                'student_roll': self.recipient.roll_number,
                'has_checked_in': today_attendance is not None,
                'check_in_time': today_attendance.check_in_time if today_attendance else None,
                'status': today_attendance.status if today_attendance else None,
            })
        return context


class WeeklyReportTemplate(EmailTemplate):
    """Weekly attendance report template"""

    subject = "Your Weekly Attendance Report"
    template_name = "emails/weekly_report.html"

    def get_context(self):
        context = super().get_context()
        if isinstance(self.recipient, Student):
            # Get weekly statistics
            week_ago = date.today() - timedelta(days=7)
            week_records = Attendance.objects.filter(
                student=self.recipient,
                date__gte=week_ago
            )

            context.update({
                'student_name': self.recipient.name,
                'student_roll': self.recipient.roll_number,
                'week_start': week_ago,
                'week_end': date.today(),
                'total_days': week_records.count(),
                'present_days': week_records.filter(status='Present').count(),
                'absent_days': week_records.filter(status='Absent').count(),
                'late_days': week_records.filter(status='Late').count(),
                'attendance_percentage': round(
                    (week_records.filter(status='Present').count() / 
                     max(week_records.count(), 1) * 100)
                ),
            })
        return context


class MonthlyReportTemplate(EmailTemplate):
    """Monthly attendance report template"""

    subject = "Your Monthly Attendance Report"
    template_name = "emails/monthly_report.html"

    def get_context(self):
        context = super().get_context()
        if isinstance(self.recipient, Student):
            # Get monthly statistics
            month_start = date.today().replace(day=1)
            month_records = Attendance.objects.filter(
                student=self.recipient,
                date__gte=month_start
            )

            context.update({
                'student_name': self.recipient.name,
                'student_roll': self.recipient.roll_number,
                'month': date.today().strftime('%B %Y'),
                'total_days': month_records.count(),
                'present_days': month_records.filter(status='Present').count(),
                'absent_days': month_records.filter(status='Absent').count(),
                'late_days': month_records.filter(status='Late').count(),
                'attendance_percentage': round(
                    (month_records.filter(status='Present').count() / 
                     max(month_records.count(), 1) * 100)
                ),
            })
        return context


class LowAttendanceAlertTemplate(EmailTemplate):
    """Low attendance warning template"""

    subject = "Alert: Your Attendance is Below Threshold"
    template_name = "emails/low_attendance_alert.html"

    def __init__(self, recipient=None, context=None, threshold=75):
        super().__init__(recipient, context)
        self.threshold = threshold

    def get_context(self):
        context = super().get_context()
        if isinstance(self.recipient, Student):
            # Calculate attendance percentage
            all_records = Attendance.objects.filter(student=self.recipient)
            present_count = all_records.filter(status='Present').count()
            total_count = all_records.count()
            attendance_percent = (present_count / total_count * 100) if total_count > 0 else 0

            context.update({
                'student_name': self.recipient.name,
                'student_roll': self.recipient.roll_number,
                'attendance_percentage': round(attendance_percent),
                'threshold': self.threshold,
                'present_days': present_count,
                'total_days': total_count,
                'urgent': attendance_percent < self.threshold,
            })
        return context


class CheckInConfirmationTemplate(EmailTemplate):
    """Check-in confirmation template"""

    subject = "Attendance Check-in Confirmed"
    template_name = "emails/check_in_confirmation.html"

    def get_context(self):
        context = super().get_context()
        if isinstance(self.recipient, Student):
            today_attendance = Attendance.objects.filter(
                student=self.recipient,
                date=date.today()
            ).first()

            context.update({
                'student_name': self.recipient.name,
                'student_roll': self.recipient.roll_number,
                'check_in_time': today_attendance.check_in_time if today_attendance else None,
                'status': today_attendance.status if today_attendance else None,
                'date': date.today(),
            })
        return context


class TeacherNotificationTemplate(EmailTemplate):
    """Teacher notification template"""

    subject = "Class Attendance Summary"
    template_name = "emails/teacher_notification.html"

    def __init__(self, recipient=None, context=None, class_name=None):
        super().__init__(recipient, context)
        self.class_name = class_name

    def get_context(self):
        context = super().get_context()

        if self.class_name:
            from app1.models import Student

            students = Student.objects.filter(student_class__icontains=self.class_name)
            today_records = Attendance.objects.filter(
                student__in=students,
                date=date.today()
            )

            context.update({
                'class_name': self.class_name,
                'total_students': students.count(),
                'present_today': today_records.filter(status='Present').count(),
                'absent_today': today_records.filter(status='Absent').count(),
                'late_today': today_records.filter(status='Late').count(),
                'attendance_percentage': round(
                    (today_records.filter(status='Present').count() / 
                     max(students.count(), 1) * 100)
                ),
                'date': date.today(),
            })
        return context


class BulkEmailService:
    """Service for sending bulk emails"""

    @staticmethod
    def send_bulk_template(template_class, recipients, **template_kwargs):
        """Send template to multiple recipients"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for recipient in recipients:
            try:
                template = template_class(recipient=recipient, **template_kwargs)
                if template.send():
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send to {recipient}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error sending to {recipient}: {str(e)}")
                logger.error(f"Bulk email error: {str(e)}")

        logger.info(
            f"Bulk email complete: {results['success']} sent, {results['failed']} failed"
        )
        return results

    @staticmethod
    def send_daily_reminders(authorized_only=True):
        """Send daily reminders to all students"""
        students = Student.objects.all()
        if authorized_only:
            students = students.filter(authorized=True)

        return BulkEmailService.send_bulk_template(
            DailyReminderTemplate,
            list(students)
        )

    @staticmethod
    def send_weekly_reports(authorized_only=True):
        """Send weekly reports to all students"""
        students = Student.objects.all()
        if authorized_only:
            students = students.filter(authorized=True)

        return BulkEmailService.send_bulk_template(
            WeeklyReportTemplate,
            list(students)
        )

    @staticmethod
    def send_monthly_reports(authorized_only=True):
        """Send monthly reports to all students"""
        students = Student.objects.all()
        if authorized_only:
            students = students.filter(authorized=True)

        return BulkEmailService.send_bulk_template(
            MonthlyReportTemplate,
            list(students)
        )

    @staticmethod
    def send_low_attendance_alerts(threshold=75):
        """Send alerts to students with low attendance"""
        students = Student.objects.all()
        affected_students = []

        for student in students:
            records = Attendance.objects.filter(student=student)
            if records.count() > 0:
                percent = (records.filter(status='Present').count() / records.count() * 100)
                if percent < threshold:
                    affected_students.append(student)

        return BulkEmailService.send_bulk_template(
            LowAttendanceAlertTemplate,
            affected_students,
            threshold=threshold
        )

    @staticmethod
    def send_authorization_emails(student_ids):
        """Send authorization emails to students"""
        students = Student.objects.filter(id__in=student_ids)
        return BulkEmailService.send_bulk_template(
            AuthorizationTemplate,
            list(students)
        )


class TemplateCustomizer:
    """Customize email templates"""

    CUSTOM_TEMPLATES = {}

    @classmethod
    def register_template(cls, template_id, template_class):
        """Register custom template"""
        cls.CUSTOM_TEMPLATES[template_id] = template_class
        logger.info(f"Template registered: {template_id}")

    @classmethod
    def get_template(cls, template_id):
        """Get registered template"""
        return cls.CUSTOM_TEMPLATES.get(template_id)

    @classmethod
    def list_templates(cls):
        """List all registered templates"""
        return list(cls.CUSTOM_TEMPLATES.keys())

    @classmethod
    def update_subject(cls, template_id, new_subject):
        """Update template subject"""
        if template_id in cls.CUSTOM_TEMPLATES:
            cls.CUSTOM_TEMPLATES[template_id].subject = new_subject
            logger.info(f"Template subject updated: {template_id}")
            return True
        return False
