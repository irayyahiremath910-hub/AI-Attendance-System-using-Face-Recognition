"""Pagination and Ordering Configuration for REST API

This module provides custom pagination classes and ordering configuration
to ensure consistent pagination and sorting across all API endpoints.
"""

from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination
from rest_framework.response import Response
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """Standard page-number based pagination."""
    page_size = 20
    page_size_query_param = 'page_size'
    page_size_query_description = 'Number of results to return per page. Max: 100'
    max_page_size = 100
    page_query_description = 'A page number within the paginated result set.'
    
    def get_paginated_response(self, data):
        """Custom paginated response format."""
        return Response(OrderedDict([
            ('total_count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.page_size),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class LargeResultSetPagination(LimitOffsetPagination):
    """Limit-offset pagination for large result sets."""
    default_limit = 50
    limit_query_param = 'limit'
    limit_query_description = 'Number of results to return.'
    offset_query_param = 'offset'
    offset_query_description = 'The initial index from which to return the results.'
    max_limit = 200
    
    def get_paginated_response(self, data):
        """Custom paginated response format."""
        return Response(OrderedDict([
            ('total_count', self.count),
            ('limit', self.limit),
            ('offset', self.offset),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class StudentCursorPagination(CursorPagination):
    """Cursor-based pagination for efficient large dataset pagination."""
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-id'  # Must be set
    cursor_query_param = 'cursor'
    cursor_query_description = 'The pagination cursor value.'


class AttendanceCursorPagination(CursorPagination):
    """Cursor-based pagination for attendance records."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    ordering = '-date'  # Most recent first
    cursor_query_param = 'cursor'


# Ordering configuration for different models
class StandardOrdering:
    """Standard ordering options."""
    
    # Student ordering fields
    STUDENT_ORDERING_FIELDS = [
        'id',
        'name',
        'email',
        'created_at',
        '-created_at',
        'student_class',
    ]
    
    # Attendance ordering fields
    ATTENDANCE_ORDERING_FIELDS = [
        'id',
        'date',
        '-date',
        'student__name',
        'check_in_time',
        '-check_in_time',
        'check_out_time',
        '-check_out_time',
    ]
    
    # Default ordering
    STUDENT_DEFAULT_ORDERING = ['-created_at']
    ATTENDANCE_DEFAULT_ORDERING = ['-date', '-check_in_time']


def get_ordering_help_text():
    """Get help text for ordering parameter."""
    return """Order results. Prefix with '-' for descending. 
    For students: id, name, email, created_at, student_class.
    For attendance: id, date, student__name, check_in_time, check_out_time."""
