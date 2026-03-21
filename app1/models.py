from django.db import models
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import timedelta

class Student(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=15)
    student_class = models.CharField(max_length=100, db_index=True)
    image = models.ImageField(upload_to='students/')
    authorized = models.BooleanField(default=False, db_index=True)
    face_encoding = models.JSONField(null=True, blank=True)  # Cache face encoding
    encoding_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['authorized', 'name']),
            models.Index(fields=['student_class', 'authorized']),
        ]

    def __str__(self):
        return self.name

    def get_attendance_percentage(self, days=30):
        """Calculate attendance percentage for last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        total_days = Attendance.objects.filter(
            student=self, 
            date__range=[start_date, end_date]
        ).count()
        
        present_days = Attendance.objects.filter(
            student=self, 
            date__range=[start_date, end_date],
            check_in_time__isnull=False
        ).count()
        
        if total_days == 0:
            return 0
        
        return (present_days / total_days) * 100

    def is_low_attendance(self, threshold=75):
        """Check if attendance is below threshold"""
        return self.get_attendance_percentage() < threshold


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records', db_index=True)
    date = models.DateField(db_index=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')],
        default='absent'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'date')
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['student', 'date']),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.date}"

    def mark_checked_in(self):
        self.check_in_time = timezone.now()
        self.status = 'present'
        self.save()

    def mark_checked_out(self):
        if self.check_in_time:
            self.check_out_time = timezone.now()
            self.save()
        else:
            raise ValueError("Cannot mark check-out without check-in.")

    def calculate_duration(self):
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        return None

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.date = timezone.now().date()
        super().save(*args, **kwargs)


class AttendanceSummary(models.Model):
    """Daily attendance summary for quick reporting"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_summary', db_index=True)
    month = models.CharField(max_length=7)  # YYYY-MM format
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    late_days = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'month')
        indexes = [
            models.Index(fields=['month', 'percentage']),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.month}"


class CameraConfiguration(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Give a name to this camera configuration", db_index=True)
    camera_source = models.CharField(max_length=255, help_text="Camera index (0 for default webcam or RTSP/HTTP URL for IP camera)")
    threshold = models.FloatField(default=0.6, help_text="Face recognition confidence threshold")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]

    def __str__(self):
        return self.name


class AttendanceAlert(models.Model):
    """Send alerts for low attendance"""
    ALERT_TYPES = [
        ('low_attendance', 'Low Attendance'),
        ('absent_week', 'Absent for a Week'),
        ('absent_day', 'Absent Today'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.name} - {self.alert_type}"
