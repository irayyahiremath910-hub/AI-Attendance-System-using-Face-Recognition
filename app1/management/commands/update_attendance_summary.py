from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app1.models import Student, Attendance, AttendanceSummary
from django.db.models import Count


class Command(BaseCommand):
    help = 'Update monthly attendance summaries'

    def add_arguments(self, parser):
        parser.add_argument('--month', type=str, help='Month to update (YYYY-MM format)')

    def handle(self, *args, **options):
        month = options.get('month')
        
        if not month:
            today = timezone.now().date()
            month = today.strftime('%Y-%m')
        
        self.stdout.write(f'Updating attendance summary for {month}...')
        
        year, month_num = month.split('-')
        year = int(year)
        month_num = int(month_num)
        
        students = Student.objects.filter(authorized=True)
        updated = 0
        
        for student in students:
            # Count attendance for the month
            month_attendance = Attendance.objects.filter(
                student=student,
                date__year=year,
                date__month=month_num
            )
            
            present_days = month_attendance.filter(check_in_time__isnull=False).count()
            absent_days = month_attendance.filter(check_in_time__isnull=True).count()
            late_days = month_attendance.filter(status='late').count()
            
            total_days = present_days + absent_days
            percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            summary, created = AttendanceSummary.objects.update_or_create(
                student=student,
                month=month,
                defaults={
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'late_days': late_days,
                    'percentage': percentage
                }
            )
            updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated} attendance summaries for {month}')
        )
