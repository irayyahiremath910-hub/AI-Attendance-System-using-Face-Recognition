"""
Analytics API Views for attendance reporting and insights
Appended to api_views.py
"""

# Add this to the end of app1/api_views.py


class AnalyticsView(APIView):
    """Analytics endpoints for attendance reporting"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get main analytics dashboard"""
        report = AttendanceAnalyticsService.get_attendance_summary_report()
        return Response(report, status=status.HTTP_200_OK)

    def post(self, request):
        """Get custom analytics for date range"""
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        from datetime import datetime
        
        if start_date:
            start_date = datetime.fromisoformat(start_date).date()
        if end_date:
            end_date = datetime.fromisoformat(end_date).date()
        
        report = AttendanceAnalyticsService.get_attendance_summary_report(start_date, end_date)
        return Response(report, status=status.HTTP_200_OK)


class DepartmentAnalyticsView(APIView):
    """Department-wise analytics"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get department statistics"""
        stats = AttendanceAnalyticsService.get_department_statistics()
        return Response({
            'departments': stats,
            'total_departments': len(stats)
        }, status=status.HTTP_200_OK)


class SystemHealthView(APIView):
    """System health and status monitoring"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get system health metrics"""
        metrics = AttendanceAnalyticsService.get_system_health_metrics()
        return Response(metrics, status=status.HTTP_200_OK)


class AttendanceForecastView(APIView):
    """Attendance forecasting"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get attendance forecast for next 7 days"""
        forecast = AttendanceAnalyticsService.get_attendance_forecast()
        return Response({
            'forecast_days': 7,
            'predictions': forecast
        }, status=status.HTTP_200_OK)


class StudentAnalyticsDetailView(APIView):
    """Individual student analytics"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        """Get analytics for specific student"""
        try:
            student = Student.objects.get(id=student_id)
            days = int(request.query_params.get('days', 30))
            
            metrics = AttendanceAnalyticsService.get_student_attendance_metrics(student, days)
            return Response(metrics, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class LowAttendanceView(APIView):
    """Identify low attendance students"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get students with low attendance"""
        threshold = int(request.query_params.get('threshold', 70))
        days = int(request.query_params.get('days', 30))
        
        students = AttendanceAnalyticsService.identify_low_attendance_students(threshold, days)
        
        return Response({
            'threshold': threshold,
            'days': days,
            'low_attendance_students': students,
            'count': len(students)
        }, status=status.HTTP_200_OK)


class AttendanceTrendsView(APIView):
    """Daily attendance trends"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get attendance trends"""
        days = int(request.query_params.get('days', 30))
        trends = AttendanceAnalyticsService.get_daily_trends(days)
        
        return Response({
            'period_days': days,
            'trends': trends
        }, status=status.HTTP_200_OK)


class PeakHoursView(APIView):
    """Peak check-in hours analysis"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get peak hours for check-in"""
        peak_hours = AttendanceAnalyticsService.get_peak_hours()
        
        return Response({
            'analysis_days': 7,
            'peak_hours': peak_hours
        }, status=status.HTTP_200_OK)
