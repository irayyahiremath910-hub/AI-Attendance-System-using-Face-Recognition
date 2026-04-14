"""
Tests for Attendance Service
"""

import pytest
from app1.services.attendance import AttendanceService
from app1.models import Student, Attendance
from django.utils import timezone
from datetime import datetime, date, timedelta


class TestAttendanceService:
    """Test cases for AttendanceService"""

    def test_mark_check_in(self, test_student):
        """Test marking student as checked in"""
        today = date.today()
        result = AttendanceService.mark_check_in(test_student, today)
        
        assert result is not None
        assert result.check_in_time is not None
        assert result.check_out_time is None

    def test_mark_check_out_success(self, test_attendance):
        """Test marking student as checked out"""
        test_attendance.check_in_time = timezone.now() - timedelta(hours=8)
        test_attendance.save()
        
        today = date.today()
        result = AttendanceService.mark_check_out(test_attendance.student, today)
        
        assert result is not None
        assert result.check_out_time is not None

    def test_can_check_out_validation(self, test_student):
        """Test check-out validation rules"""
        today = date.today()
        
        # Not checked in yet
        can_checkout = AttendanceService.can_check_out(test_student, today)
        assert can_checkout is False or can_checkout == 'Already checked out'

    def test_get_attendance_status(self, test_student):
        """Test getting student attendance status"""
        status = AttendanceService.get_attendance_status(test_student)
        assert status is not None
        assert isinstance(status, dict)

    def test_get_student_attendance_history(self, test_student, test_attendance):
        """Test getting student attendance history"""
        history = AttendanceService.get_student_attendance_history(test_student, days=30)
        assert history.exists()
        assert history[0].student == test_student

    def test_get_daily_attendance_summary(self):
        """Test getting daily attendance summary"""
        summary = AttendanceService.get_daily_attendance_summary(date.today())
        assert summary is not None

    def test_duplicate_check_in_prevention(self, test_student):
        """Test preventing duplicate check-ins on same day"""
        today = date.today()
        
        # First check-in
        first = AttendanceService.mark_check_in(test_student, today)
        assert first is not None
        
        # Try second check-in same day (should get existing record)
        second = AttendanceService.mark_check_in(test_student, today)
        assert first.id == second.id


class TestAttendanceModel:
    """Test cases for Attendance model"""

    def test_attendance_creation(self, test_student):
        """Test creating attendance record"""
        attendance = Attendance.objects.create(
            student=test_student,
            date=date.today()
        )
        assert attendance is not None
        assert attendance.date == date.today()

    def test_attendance_duration_calculation(self, test_attendance):
        """Test attendance duration calculation"""
        test_attendance.check_in_time = timezone.now() - timedelta(hours=8, minutes=30)
        test_attendance.check_out_time = timezone.now()
        test_attendance.save()
        
        duration = test_attendance.calculate_duration()
        assert duration is not None
        assert '8h' in duration

    def test_attendance_auto_date_assignment(self, test_student):
        """Test automatic date assignment on creation"""
        attendance = Attendance(student=test_student)
        attendance.save()
        
        assert attendance.date == date.today()

    def test_attendance_mark_checked_in(self, test_attendance):
        """Test mark_checked_in method"""
        test_attendance.mark_checked_in()
        assert test_attendance.check_in_time is not None

    def test_attendance_mark_checked_out(self, test_attendance):
        """Test mark_checked_out method"""
        test_attendance.mark_checked_in()
        test_attendance.mark_checked_out()
        assert test_attendance.check_out_time is not None

    def test_attendance_checkout_without_checkin_raises_error(self, test_student):
        """Test checking out without check-in raises error"""
        attendance = Attendance.objects.create(
            student=test_student,
            date=date.today()
        )
        
        with pytest.raises(ValueError):
            attendance.mark_checked_out()
