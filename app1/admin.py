from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Attendance, CameraConfiguration, AttendanceSummary, AttendanceAlert


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'student_class', 'authorized_status', 'get_attendance_percentage']
    list_filter = ['student_class', 'authorized', 'created_at']
    search_fields = ['name', 'email', 'student_class']
    readonly_fields = ['created_at', 'updated_at', 'encoding_updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone_number', 'student_class')
        }),
        ('Authorization', {
            'fields': ('authorized',)
        }),
        ('Photo', {
            'fields': ('image',)
        }),
        ('Face Recognition', {
            'fields': ('face_encoding', 'encoding_updated_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def authorized_status(self, obj):
        if obj.authorized:
            return format_html('<span style="color: green;">✓ Authorized</span>')
        return format_html('<span style="color: red;">✗ Not Authorized</span>')
    authorized_status.short_description = 'Authorization Status'

    def get_attendance_percentage(self, obj):
        percentage = obj.get_attendance_percentage()
        if percentage >= 75:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<span style="color: {color};">{percentage:.1f}%</span>')
    get_attendance_percentage.short_description = 'Attendance %'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'check_in_time', 'check_out_time', 'status', 'duration']
    list_filter = ['date', 'status', 'created_at']
    search_fields = ['student__name']
    readonly_fields = ['created_at', 'updated_at', 'calculate_duration']
    date_hierarchy = 'date'

    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Attendance Details', {
            'fields': ('date', 'check_in_time', 'check_out_time', 'status')
        }),
        ('Duration', {
            'fields': ('calculate_duration',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def duration(self, obj):
        return obj.calculate_duration() or 'N/A'
    duration.short_description = 'Duration'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['student', 'date', 'check_in_time', 'check_out_time', 'created_at', 'updated_at', 'calculate_duration']
        return ['created_at', 'updated_at', 'calculate_duration']


@admin.register(CameraConfiguration)
class CameraConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'camera_source', 'threshold', 'is_active_status', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'camera_source']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'camera_source', 'threshold', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">● Active</span>')
        return format_html('<span style="color: red;">● Inactive</span>')
    is_active_status.short_description = 'Status'


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'month', 'present_days', 'absent_days', 'late_days', 'percentage_display']
    list_filter = ['month', 'created_at']
    search_fields = ['student__name', 'month']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def percentage_display(self, obj):
        if obj.percentage >= 75:
            color = 'green'
        elif obj.percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<span style="color: {color};">{obj.percentage:.1f}%</span>')
    percentage_display.short_description = 'Attendance %'


@admin.register(AttendanceAlert)
class AttendanceAlertAdmin(admin.ModelAdmin):
    list_display = ['student', 'alert_type', 'is_sent_status', 'created_at', 'sent_at']
    list_filter = ['alert_type', 'is_sent', 'created_at']
    search_fields = ['student__name', 'message']
    readonly_fields = ['created_at', 'sent_at']

    fieldsets = (
        ('Alert Information', {
            'fields': ('student', 'alert_type', 'message')
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def is_sent_status(self, obj):
        if obj.is_sent:
            return format_html('<span style="color: green;">✓ Sent</span>')
        return format_html('<span style="color: orange;">⊙ Pending</span>')
    is_sent_status.short_description = 'Sent Status'