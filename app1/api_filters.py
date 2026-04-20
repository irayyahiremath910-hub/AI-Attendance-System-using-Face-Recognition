"""Advanced Filters for API Endpoints

This module provides custom filters for advanced searching and filtering
capabilities across the attendance system API.
"""

from django_filters import FilterSet, CharFilter, DateFilter, BooleanFilter, NumberFilter
from django_filters import rest_framework as filters
from django.db.models import Q
from app1.models import Student, Attendance
import logging

logger = logging.getLogger(__name__)


class StudentFilter(FilterSet):
    """Advanced filter for Student model."""
    
    # Name search (case-insensitive partial match)
    name = CharFilter(field_name='name', lookup_expr='icontains', help_text='Search by student name')
    
    # Email search
    email = CharFilter(field_name='email', lookup_expr='icontains', help_text='Search by email')
    
    # Class filter
    student_class = CharFilter(field_name='student_class', lookup_expr='icontains', help_text='Filter by class')
    
    # Authorization status
    authorized = BooleanFilter(field_name='authorized', help_text='Filter by authorization status')
    
    # Date range filters
    created_after = DateFilter(field_name='created_at', lookup_expr='gte', help_text='Students created after this date')
    created_before = DateFilter(field_name='created_at', lookup_expr='lte', help_text='Students created before this date')
    
    class Meta:
        model = Student
        fields = ['name', 'email', 'student_class', 'authorized', 'created_after', 'created_before']
    
    def filter_queryset(self, queryset):
        """Apply filters to queryset."""
        queryset = super().filter_queryset(queryset)
        
        # Multi-field search
        search = self.data.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(student_class__icontains=search)
            )
        
        logger.debug(f"Applied StudentFilter: {self.data}")
        return queryset


class AttendanceFilter(FilterSet):
    """Advanced filter for Attendance model."""
    
    # Student name search
    student_name = CharFilter(field_name='student__name', lookup_expr='icontains', help_text='Search by student name')
    
    # Student ID filter
    student_id = NumberFilter(field_name='student__id', help_text='Filter by student ID')
    
    # Date range filters
    date_from = DateFilter(field_name='date', lookup_expr='gte', help_text='Attendance from date')
    date_to = DateFilter(field_name='date', lookup_expr='lte', help_text='Attendance to date')
    
    # Check-in/out time filters
    has_check_in = BooleanFilter(
        field_name='check_in_time',
        method='filter_has_check_in',
        help_text='Filter records with check-in time'
    )
    
    has_check_out = BooleanFilter(
        field_name='check_out_time',
        method='filter_has_check_out',
        help_text='Filter records with check-out time'
    )
    
    class Meta:
        model = Attendance
        fields = ['student_name', 'student_id', 'date_from', 'date_to', 'has_check_in', 'has_check_out']
    
    def filter_has_check_in(self, queryset, name, value):
        """Filter by check-in presence."""
        if value:
            return queryset.filter(check_in_time__isnull=False)
        return queryset.filter(check_in_time__isnull=True)
    
    def filter_has_check_out(self, queryset, name, value):
        """Filter by check-out presence."""
        if value:
            return queryset.filter(check_out_time__isnull=False)
        return queryset.filter(check_out_time__isnull=True)
    
    def filter_queryset(self, queryset):
        """Apply filters to queryset."""
        queryset = super().filter_queryset(queryset)
        
        # Multi-field search
        search = self.data.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__name__icontains=search) |
                Q(student__email__icontains=search)
            )
        
        logger.debug(f"Applied AttendanceFilter: {self.data}")
        return queryset
