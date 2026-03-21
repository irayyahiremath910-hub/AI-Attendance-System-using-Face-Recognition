from rest_framework import serializers
from .models import Student, Attendance, CameraConfiguration, AttendanceSummary, AttendanceAlert


class StudentSerializer(serializers.ModelSerializer):
    attendance_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = ['id', 'name', 'email', 'phone_number', 'student_class', 'authorized', 'attendance_percentage', 'created_at']
        read_only_fields = ['id', 'created_at', 'attendance_percentage']

    def get_attendance_percentage(self, obj):
        return round(obj.get_attendance_percentage(), 2)


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'date', 'check_in_time', 'check_out_time', 'status', 'duration', 'created_at']
        read_only_fields = ['id', 'created_at', 'student_name', 'duration']

    def get_duration(self, obj):
        return obj.calculate_duration()


class CameraConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraConfiguration
        fields = ['id', 'name', 'camera_source', 'threshold', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AttendanceSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = AttendanceSummary
        fields = ['id', 'student', 'student_name', 'month', 'present_days', 'absent_days', 'late_days', 'percentage']
        read_only_fields = ['id', 'percentage']


class AttendanceAlertSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = AttendanceAlert
        fields = ['id', 'student', 'student_name', 'alert_type', 'message', 'is_sent', 'created_at', 'sent_at']
        read_only_fields = ['id', 'created_at', 'sent_at']


class AttendanceDetailedSerializer(serializers.ModelSerializer):
    """Detailed attendance with student info"""
    student = StudentSerializer()
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'date', 'check_in_time', 'check_out_time', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']
