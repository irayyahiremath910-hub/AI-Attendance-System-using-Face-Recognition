"""
Extended student profile management system
Manages detailed student information, documents, and preferences
"""

from django.db import models
from django.utils import timezone
from app1.models import Student
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


class StudentProfile(models.Model):
    """Extended student profile information"""

    BLOOD_GROUP_CHOICES = [
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('Other', 'Other'),
    ]

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    parent_name = models.CharField(max_length=100, blank=True)
    parent_email = models.EmailField(blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)
    aadhar_number = models.CharField(max_length=12, blank=True, unique=True)
    enrollment_date = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Student Profiles"
        ordering = ['student__name']

    def __str__(self):
        return f"Profile - {self.student.name}"

    def get_age(self):
        """Calculate student age"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def get_full_address(self):
        """Get complete address"""
        parts = [self.address, self.city, self.state, self.postal_code]
        return ', '.join(part for part in parts if part)


class StudentDocuments(models.Model):
    """Manage student documents and certificates"""

    DOCUMENT_TYPES = [
        ('AADHAR', 'Aadhar Card'),
        ('PAN', 'PAN Card'),
        ('PASSPORT', 'Passport'),
        ('LICENSE', 'License'),
        ('10TH_CERT', '10th Certificate'),
        ('12TH_CERT', '12th Certificate'),
        ('DEGREE', 'Degree Certificate'),
        ('OTHER', 'Other'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=200)
    document_file = models.FileField(upload_to='student_documents/')
    document_number = models.CharField(max_length=50, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.CharField(max_length=100, blank=True)
    verified_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.student.name} - {self.get_document_type_display()}"

    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False

    def days_until_expiry(self):
        """Get days until expiry"""
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return None


class StudentPreferences(models.Model):
    """Student preferences and settings"""

    NOTIFICATION_FREQ = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('NEVER', 'Never'),
    ]

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='preferences')
    email_notifications = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=NOTIFICATION_FREQ,
        default='WEEKLY'
    )
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=False)
    low_attendance_alerts = models.BooleanField(default=True)
    alert_threshold = models.IntegerField(default=75)  # Attendance percentage threshold
    receives_parent_emails = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Student Preferences"

    def __str__(self):
        return f"Preferences - {self.student.name}"


class StudentActivity(models.Model):
    """Track student activities and achievements"""

    ACTIVITY_TYPES = [
        ('ATTENDANCE', 'Attendance'),
        ('ACHIEVEMENT', 'Achievement'),
        ('PARTICIPATION', 'Participation'),
        ('EVENT', 'Event'),
        ('DISCIPLINARY', 'Disciplinary'),
        ('COUNSELING', 'Counseling'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    recorded_by = models.CharField(max_length=100)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.name} - {self.title}"


class StudentEmergencyInfo(models.Model):
    """Emergency contact information"""

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='emergency_info')
    primary_contact_name = models.CharField(max_length=100)
    primary_contact_phone = models.CharField(max_length=15)
    primary_contact_relation = models.CharField(max_length=50)
    secondary_contact_name = models.CharField(max_length=100, blank=True)
    secondary_contact_phone = models.CharField(max_length=15, blank=True)
    secondary_contact_relation = models.CharField(max_length=50, blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    hospital_preference = models.CharField(max_length=100, blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy = models.CharField(max_length=50, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Emergency Info - {self.student.name}"


class ProfileManager:
    """Service for managing student profiles"""

    @staticmethod
    def create_full_profile(student, profile_data, preferences_data=None):
        """Create complete student profile"""
        try:
            # Create student profile
            profile = StudentProfile.objects.create(
                student=student,
                **profile_data
            )

            # Create preferences if provided
            if preferences_data:
                StudentPreferences.objects.create(
                    student=student,
                    **preferences_data
                )

            logger.info(f"Full profile created for student {student.id}")
            return profile

        except Exception as e:
            logger.error(f"Error creating profile: {str(e)}")
            return None

    @staticmethod
    def update_profile(student_id, profile_data):
        """Update student profile"""
        try:
            profile = StudentProfile.objects.get(student_id=student_id)
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()

            logger.info(f"Profile updated for student {student_id}")
            return profile

        except StudentProfile.DoesNotExist:
            logger.error(f"Profile not found for student {student_id}")
            return None

    @staticmethod
    def get_complete_profile(student_id):
        """Get complete student profile with all related data"""
        try:
            student = Student.objects.get(id=student_id)
            profile = student.profile if hasattr(student, 'profile') else None
            documents = student.documents.all() if hasattr(student, 'documents') else []
            preferences = student.preferences if hasattr(student, 'preferences') else None
            emergency_info = student.emergency_info if hasattr(student, 'emergency_info') else None
            activities = student.activities.all() if hasattr(student, 'activities') else []

            return {
                'student': {
                    'id': student.id,
                    'name': student.name,
                    'roll_number': student.roll_number,
                    'email': student.email,
                    'class': student.student_class,
                    'authorized': student.authorized,
                },
                'profile': {
                    'date_of_birth': profile.date_of_birth if profile else None,
                    'age': profile.get_age() if profile else None,
                    'gender': profile.gender if profile else None,
                    'blood_group': profile.blood_group if profile else None,
                    'phone': profile.phone if profile else None,
                    'address': profile.get_full_address() if profile else None,
                } if profile else None,
                'documents': [{
                    'type': doc.get_document_type_display(),
                    'name': doc.document_name,
                    'number': doc.document_number,
                    'uploaded': doc.upload_date.isoformat(),
                    'verified': doc.is_verified,
                    'expired': doc.is_expired(),
                } for doc in documents],
                'preferences': {
                    'email_notifications': preferences.email_notifications if preferences else None,
                    'frequency': preferences.notification_frequency if preferences else None,
                    'alert_threshold': preferences.alert_threshold if preferences else None,
                } if preferences else None,
                'emergency_contact': {
                    'primary_name': emergency_info.primary_contact_name if emergency_info else None,
                    'primary_phone': emergency_info.primary_contact_phone if emergency_info else None,
                    'medical_conditions': emergency_info.medical_conditions if emergency_info else None,
                } if emergency_info else None,
                'recent_activities': [{
                    'type': activity.get_activity_type_display(),
                    'title': activity.title,
                    'date': activity.date.isoformat(),
                } for activity in list(activities)[:5]],
            }

        except Student.DoesNotExist:
            logger.error(f"Student {student_id} not found")
            return None

    @staticmethod
    def add_document(student_id, document_data):
        """Add document to student profile"""
        try:
            student = Student.objects.get(id=student_id)
            document = StudentDocuments.objects.create(
                student=student,
                **document_data
            )
            logger.info(f"Document added for student {student_id}")
            return document

        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return None

    @staticmethod
    def record_activity(student_id, activity_data):
        """Record student activity"""
        try:
            student = Student.objects.get(id=student_id)
            activity = StudentActivity.objects.create(
                student=student,
                **activity_data
            )
            logger.info(f"Activity recorded for student {student_id}")
            return activity

        except Exception as e:
            logger.error(f"Error recording activity: {str(e)}")
            return None

    @staticmethod
    def get_students_summary(class_name=None):
        """Get summary of all students with profile information"""
        students = Student.objects.all()
        if class_name:
            students = students.filter(student_class__icontains=class_name)

        summary = []
        for student in students:
            profile = student.profile if hasattr(student, 'profile') else None
            summary.append({
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'class': student.student_class,
                'email': student.email,
                'age': profile.get_age() if profile else None,
                'phone': profile.phone if profile else None,
                'authorized': student.authorized,
            })

        return summary

    @staticmethod
    def export_student_data(student_id):
        """Export all student data for GDPR compliance"""
        complete_profile = ProfileManager.get_complete_profile(student_id)

        if complete_profile:
            return {
                'exported_at': datetime.now().isoformat(),
                'data': complete_profile,
            }

        return None
