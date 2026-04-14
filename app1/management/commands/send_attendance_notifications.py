"""
Django management command to send attendance notifications
Usage: python manage.py send_attendance_notifications [--type=TYPE] [--student_id=ID]
"""

from django.core.management.base import BaseCommand
from app1.models import Student
from app1.notification_service import EmailNotificationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send attendance notifications to students'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['reminder', 'authorization', 'report'],
            default='reminder',
            help='Type of notification to send'
        )
        parser.add_argument(
            '--student_id',
            type=int,
            help='Send notification to specific student'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Send to all students'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Days for report (only for report type)'
        )

    def handle(self, *args, **options):
        notification_type = options.get('type', 'reminder')
        student_id = options.get('student_id')
        send_all = options.get('all', False)
        days = options.get('days', 7)

        if student_id:
            students = Student.objects.filter(id=student_id)
        elif send_all:
            students = Student.objects.all()
        else:
            students = Student.objects.filter(authorized=True)

        if not students.exists():
            self.stdout.write(
                self.style.WARNING('No students found matching criteria')
            )
            return

        success_count = 0
        failed_count = 0

        service = EmailNotificationService()

        for student in students:
            try:
                if notification_type == 'reminder':
                    result = service.send_attendance_reminder(student)
                elif notification_type == 'authorization':
                    result = service.send_student_authorization_notification(student)
                elif notification_type == 'report':
                    result = service.send_attendance_report(student, days)

                if result:
                    success_count += 1
                    self.stdout.write(f"✓ {student.email}")
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"✗ {student.email} - Failed to send")
                    )
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ {student.email} - {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n📧 Notification Summary:\n'
                f'   Successfully sent: {success_count}\n'
                f'   Failed: {failed_count}\n'
                f'   Total: {success_count + failed_count}'
            )
        )

        logger.info(
            f"Sent {success_count} {notification_type} notifications "
            f"({failed_count} failed)"
        )
