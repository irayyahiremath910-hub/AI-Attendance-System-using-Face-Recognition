# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from .models import Student, Attendance, CameraConfiguration


# ==================== CUSTOM VALIDATORS ====================

def validate_phone_number(value):
    """Validate phone number format (10-15 digits, optional +)"""
    pattern = r'^\+?1?\d{9,14}$'
    if not re.match(pattern, value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')):
        raise ValidationError(
            _('Phone number must be 10-15 digits. Example: +1 (555) 123-4567 or 5551234567'),
            code='invalid_phone'
        )


def validate_student_class(value):
    """Validate student class format"""
    if not value or len(value.strip()) < 2:
        raise ValidationError(
            _('Student class must be at least 2 characters'),
            code='invalid_class'
        )
    if len(value) > 100:
        raise ValidationError(
            _('Student class must not exceed 100 characters'),
            code='class_too_long'
        )


def validate_camera_threshold(value):
    """Validate camera threshold is between 0.0 and 1.0"""
    if not isinstance(value, (int, float)):
        raise ValidationError(
            _('Threshold must be a number'),
            code='invalid_type'
        )
    if value < 0.0 or value > 1.0:
        raise ValidationError(
            _('Threshold must be between 0.0 and 1.0'),
            code='threshold_range'
        )


def validate_camera_source(value):
    """Validate camera source (digit 0-9 or valid URL/IP)"""
    # Check if it's a digit (0-9) or looks like a URL/IP
    if value.isdigit():
        if not (0 <= int(value) <= 9):
            raise ValidationError(
                _('Camera index must be 0-9 for built-in cameras'),
                code='invalid_index'
            )
    elif not (value.startswith('http://') or value.startswith('https://') or value.startswith('rtsp://')):
        raise ValidationError(
            _('Invalid camera source. Use camera index (0-9) or valid URL (http://, https://, rtsp://)'),
            code='invalid_source'
        )


# ==================== FORM CLASSES ====================

class StudentForm(forms.ModelForm):
    """Form for creating and updating student records"""
    
    class Meta:
        model = Student
        fields = ['name', 'email', 'phone_number', 'student_class', 'image', 'authorized']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'student@example.com',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567 or 5551234567',
                'required': True
            }),
            'student_class': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Class A, Grade 10',
                'required': True
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': False
            }),
            'authorized': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            })
        }

    def clean_name(self):
        """Validate name field"""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError(_('Name is required'), code='required')
        if len(name) < 2:
            raise ValidationError(_('Name must be at least 2 characters'), code='too_short')
        if len(name) > 255:
            raise ValidationError(_('Name must not exceed 255 characters'), code='too_long')
        return name

    def clean_email(self):
        """Validate email uniqueness and format"""
        email = self.cleaned_data.get('email', '').lower()
        if not email:
            raise ValidationError(_('Email is required'), code='required')
        
        # Check if email already exists (excluding current instance)
        existing = Student.objects.filter(email=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError(
                _('A student with this email already exists'),
                code='email_exists'
            )
        return email

    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone:
            raise ValidationError(_('Phone number is required'), code='required')
        
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Validation will be done by custom validator
        validate_phone_number(phone)
        return phone

    def clean_student_class(self):
        """Validate student class"""
        student_class = self.cleaned_data.get('student_class', '').strip()
        if not student_class:
            raise ValidationError(_('Student class is required'), code='required')
        
        validate_student_class(student_class)
        return student_class

    def clean_image(self):
        """Validate image field"""
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError(
                    _('Image file size must not exceed 5MB'),
                    code='file_too_large'
                )
            # Check file type
            if not image.name.lower().endswith(('jpg', 'jpeg', 'png', 'gif')):
                raise ValidationError(
                    _('Only JPG, PNG, and GIF images are allowed'),
                    code='invalid_format'
                )
        return image


class CameraConfigurationForm(forms.ModelForm):
    """Form for configuring camera settings"""
    
    class Meta:
        model = CameraConfiguration
        fields = ['name', 'camera_source', 'threshold']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Front Door Camera',
                'required': True
            }),
            'camera_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0 for webcam or rtsp://camera-url',
                'required': True
            }),
            'threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.6 (0.0-1.0)',
                'min': '0.0',
                'max': '1.0',
                'step': '0.01',
                'required': True
            })
        }

    def clean_name(self):
        """Validate camera name"""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError(_('Camera name is required'), code='required')
        if len(name) < 2:
            raise ValidationError(_('Camera name must be at least 2 characters'), code='too_short')
        if len(name) > 100:
            raise ValidationError(_('Camera name must not exceed 100 characters'), code='too_long')
        
        # Check uniqueness (excluding current instance)
        existing = CameraConfiguration.objects.filter(name=name)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError(
                _('A camera with this name already exists'),
                code='name_exists'
            )
        return name

    def clean_camera_source(self):
        """Validate camera source"""
        source = self.cleaned_data.get('camera_source', '').strip()
        if not source:
            raise ValidationError(_('Camera source is required'), code='required')
        
        validate_camera_source(source)
        return source

    def clean_threshold(self):
        """Validate threshold"""
        threshold = self.cleaned_data.get('threshold')
        if threshold is None:
            raise ValidationError(_('Threshold is required'), code='required')
        
        validate_camera_threshold(threshold)
        return threshold


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        empty_label="-- All Students --",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From Date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To Date'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', '-- All Status --'),
            ('checked_in', 'Checked In'),
            ('checked_out', 'Checked Out'),
            ('both', 'Both Check-in & Check-out'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def clean(self):
        """Validate filter form"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                _('From date must be before or equal to To date'),
                code='invalid_date_range'
            )
        
        return cleaned_data


class StudentAuthorizationForm(forms.Form):
    """Form for authorizing/unauthorizing students"""
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    authorize = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Authorize this student'
    )
