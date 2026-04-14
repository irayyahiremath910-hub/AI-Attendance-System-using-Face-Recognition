"""
Django management command to authorize students in bulk
Usage: python manage.py bulk_authorize_students [--count=N] [--department=DEPT] [--all]
"""

from django.core.management.base import BaseCommand
from app1.models import Student
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Authorize students in bulk for face recognition'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of unauthorized students to authorize (default: 10)'
        )
        parser.add_argument(
            '--department',
            type=str,
            help='Authorize students from specific department'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Authorize all unauthorized students'
        )
        parser.add_argument(
            '--face-required',
            action='store_true',
            help='Only authorize students with face encodings'
        )

    def handle(self, *args, **options):
        count = options.get('count', 10)
        department = options.get('department')
        authorize_all = options.get('all', False)
        face_required = options.get('face_required', False)

        # Build query
        queryset = Student.objects.filter(authorized=False)

        if department:
            queryset = queryset.filter(student_class__icontains=department)

        if face_required:
            queryset = queryset.exclude(face_encoding__isnull=True)

        if authorize_all:
            count = queryset.count()
        else:
            queryset = queryset[:count]

        total = queryset.count()

        if total == 0:
            self.stdout.write(
                self.style.WARNING('No students found matching criteria')
            )
            return

        # Authorize students
        updated = queryset.update(authorized=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully authorized {updated} students'
            )
        )

        # Print breakdown
        total_authorized = Student.objects.filter(authorized=True).count()
        total_students = Student.objects.count()

        self.stdout.write(
            f'📊 Authorization Status:\n'
            f'   Total Authorized: {total_authorized}/{total_students}\n'
            f'   Authorization Rate: {round((total_authorized/total_students*100) if total_students > 0 else 0, 2)}%'
        )

        logger.info(f"Bulk authorized {updated} students")
