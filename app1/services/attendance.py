"""Attendance Service

This service handles all attendance-related operations including
marking check-in/check-out times and managing attendance records.
"""

from app1.models import Student, Attendance
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for managing student attendance records."""

    @staticmethod
    def get_or_create_attendance(student, date=None):
        """Get or create attendance record for a student on given date.
        
        Args:
            student (Student): Student object
            date (date): Date for attendance (defaults to today)
            
        Returns:
            tuple: (Attendance object, created boolean)
        """
        if date is None:
            date = datetime.now().date()

        try:
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                date=date
            )
            logger.debug(f"Attendance record {'created' if created else 'retrieved'} for {student.name} on {date}")
            return attendance, created
        except Exception as e:
            logger.error(f"Error getting/creating attendance for {student.name}: {e}")
            return None, False

    @staticmethod
    def mark_check_in(student, date=None):
        """Mark student as checked in.
        
        Args:
            student (Student): Student object
            date (date): Date for attendance (defaults to today)
            
        Returns:
            Attendance: Updated attendance object or None
        """
        try:
            attendance, created = AttendanceService.get_or_create_attendance(student, date)
            if attendance:
                attendance.mark_checked_in()
                logger.info(f"Student {student.name} checked in at {attendance.check_in_time}")
                return attendance
        except Exception as e:
            logger.error(f"Error marking check-in for {student.name}: {e}")
        return None

    @staticmethod
    def mark_check_out(student, date=None):
        """Mark student as checked out.
        
        Args:
            student (Student): Student object
            date (date): Date for attendance (defaults to today)
            
        Returns:
            Attendance: Updated attendance object or None
        """
        try:
            attendance, _ = AttendanceService.get_or_create_attendance(student, date)
            if attendance and attendance.check_in_time and not attendance.check_out_time:
                attendance.mark_checked_out()
                logger.info(f"Student {student.name} checked out at {attendance.check_out_time}")
                return attendance
            elif attendance:
                logger.warning(f"Cannot check out {student.name}: not properly checked in")
        except Exception as e:
            logger.error(f"Error marking check-out for {student.name}: {e}")
        return None

    @staticmethod
    def can_check_out(student, date=None, min_duration_seconds=60):
        """Check if student can be checked out.
        
        Args:
            student (Student): Student object
            date (date): Date for attendance (defaults to today)
            min_duration_seconds (int): Minimum time before allowing check-out
            
        Returns:
            bool: True if student can check out, False otherwise
        """
        try:
            attendance, _ = AttendanceService.get_or_create_attendance(student, date)
            if not attendance:
                return False

            if not attendance.check_in_time or attendance.check_out_time:
                return False

            # Check if minimum duration has passed
            elapsed = timezone.now() - attendance.check_in_time
            return elapsed >= timedelta(seconds=min_duration_seconds)
        except Exception as e:
            logger.error(f"Error checking checkout eligibility for {student.name}: {e}")
            return False

    @staticmethod
    def get_attendance_status(student, date=None):
        """Get current attendance status for a student.
        
        Args:
            student (Student): Student object
            date (date): Date for attendance (defaults to today)
            
        Returns:
            dict: Status information with keys: checked_in, checked_out, check_in_time, check_out_time
        """
        try:
            attendance, _ = AttendanceService.get_or_create_attendance(student, date)
            if not attendance:
                return {
                    'checked_in': False,
                    'checked_out': False,
                    'check_in_time': None,
                    'check_out_time': None
                }

            return {
                'checked_in': attendance.check_in_time is not None,
                'checked_out': attendance.check_out_time is not None,
                'check_in_time': attendance.check_in_time,
                'check_out_time': attendance.check_out_time
            }
        except Exception as e:
            logger.error(f"Error getting attendance status for {student.name}: {e}")
            return {
                'checked_in': False,
                'checked_out': False,
                'check_in_time': None,
                'check_out_time': None
            }

    @staticmethod
    def get_student_attendance_history(student, days=30):
        """Get attendance history for a student for the past N days.
        
        Args:
            student (Student): Student object
            days (int): Number of days to retrieve (default: 30)
            
        Returns:
            queryset: Attendance records for the student
        """
        try:
            start_date = timezone.now().date() - timedelta(days=days)
            attendance_records = Attendance.objects.filter(
                student=student,
                date__gte=start_date
            ).order_by('-date')
            return attendance_records
        except Exception as e:
            logger.error(f"Error getting attendance history for {student.name}: {e}")
            return Attendance.objects.none()

    @staticmethod
    def get_daily_attendance_summary(date=None):
        """Get attendance summary for all students on a given date.
        
        Args:
            date (date): Date for summary (defaults to today)
            
        Returns:
            dict: Summary statistics including total students, checked in, checked out
        """
        if date is None:
            date = datetime.now().date()

        try:
            all_records = Attendance.objects.filter(date=date)
            checked_in = all_records.filter(check_in_time__isnull=False).count()
            checked_out = all_records.filter(check_out_time__isnull=False).count()

            return {
                'date': date,
                'total_attendance_records': all_records.count(),
                'checked_in': checked_in,
                'checked_out': checked_out,
                'pending_checkout': checked_in - checked_out
            }
        except Exception as e:
            logger.error(f"Error getting daily attendance summary: {e}")
            return {}
