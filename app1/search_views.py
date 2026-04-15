"""
Advanced search and export API views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from app1.models import Student, Attendance
from app1.serializers import StudentSerializer, AttendanceSerializer
from app1.search_service import AttendanceSearchService
import logging

logger = logging.getLogger(__name__)


class SearchAPIView(APIView):
    """Advanced search for students and attendance"""
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Search students with advanced filters"""
        query = request.data.get('query', '')
        filters = request.data.get('filters', {})
        search_type = request.data.get('type', 'student')

        if search_type == 'student':
            queryset = AttendanceSearchService.search_students(query, filters)
            serializer = StudentSerializer(queryset, many=True)
            return Response({
                'results_count': queryset.count(),
                'results': serializer.data
            })

        elif search_type == 'attendance':
            queryset = AttendanceSearchService.search_attendance(filters)
            serializer = AttendanceSerializer(queryset, many=True)
            return Response({
                'results_count': queryset.count(),
                'results': serializer.data
            })

        return Response(
            {'error': 'Invalid search type'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ExportAPIView(APIView):
    """Export data to CSV"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """Export data based on type and filters"""
        export_type = request.data.get('type')  # 'students', 'attendance', 'analytics'
        filters = request.data.get('filters', {})

        if export_type == 'students':
            queryset = AttendanceSearchService.search_students(
                request.data.get('query', ''),
                filters
            )
            return AttendanceSearchService.export_students_to_csv(queryset)

        elif export_type == 'attendance':
            queryset = AttendanceSearchService.search_attendance(filters)
            return AttendanceSearchService.export_attendance_to_csv(queryset)

        else:
            return Response(
                {'error': 'Invalid export type'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SearchSuggestionsAPIView(APIView):
    """Get search suggestions for autocomplete"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get search suggestions"""
        query = request.query_params.get('q', '')
        search_type = request.query_params.get('type', 'student')

        if not query or len(query) < 2:
            return Response({'suggestions': []})

        suggestions = AttendanceSearchService.get_advanced_search_suggestions(query, search_type)
        return Response({'suggestions': suggestions})


class AdvancedFilterAPIView(APIView):
    """Get available filters for advanced search"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get available filter options"""
        departments = Student.objects.values_list('student_class', flat=True).distinct()

        return Response({
            'filters': {
                'departments': list(departments),
                'authorization_status': [
                    {'value': True, 'label': 'Authorized'},
                    {'value': False, 'label': 'Not Authorized'}
                ],
                'face_recognition_status': [
                    {'value': True, 'label': 'Face Recognized'},
                    {'value': False, 'label': 'Face Not Recognized'}
                ],
                'attendance_status': [
                    {'value': 'checked_in', 'label': 'Checked In'},
                    {'value': 'checked_out', 'label': 'Checked Out'},
                    {'value': 'absent', 'label': 'Absent'}
                ]
            }
        })
