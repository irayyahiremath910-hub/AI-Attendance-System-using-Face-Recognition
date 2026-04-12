"""Serializers for API data serialization

This module contains serializers for converting model instances
to and from JSON format, useful for API responses.
"""

from rest_framework import serializers
from app1.models import Student, Attendance


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model."""

    class Meta:
        model = Student
        fields = ['id', 'name', 'email', 'phone_number', 'student_class', 'authorized', 'created_at']
        read_only_fields = ['id', 'created_at']


class StudentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Student model with attendance info."""

    total_attendance = serializers.SerializerMethodField()
    latest_attendance = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'name', 'email', 'phone_number', 'student_class', 'authorized', 'image', 'created_at', 'total_attendance', 'latest_attendance']
        read_only_fields = ['id', 'created_at', 'total_attendance', 'latest_attendance']

    def get_total_attendance(self, obj):
        """Get total attendance count for the student."""
        return obj.attendance_set.count()

    def get_latest_attendance(self, obj):
        """Get latest attendance record."""
        latest = obj.attendance_set.order_by('-date').first()
        if latest:
            return AttendanceSerializer(latest).data
        return None


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model."""

    student_name = serializers.CharField(source='student.name', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'date', 'check_in_time', 'check_out_time', 'duration', 'created_at']
        read_only_fields = ['id', 'student_name', 'duration', 'created_at']

    def get_duration(self, obj):
        """Calculate duration between check-in and check-out."""
        if obj.check_in_time and obj.check_out_time:
            delta = obj.check_out_time - obj.check_in_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes = remainder // 60
            return f"{hours}h {minutes}m"
        return None


class AttendanceSummarySerializer(serializers.Serializer):
    """Serializer for attendance summary data."""

    date = serializers.DateField()
    total_students = serializers.IntegerField()
    checked_in = serializers.IntegerField()
    checked_out = serializers.IntegerField()
    pending_checkout = serializers.IntegerField()
