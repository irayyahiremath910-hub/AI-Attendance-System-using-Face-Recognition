"""
Admin Dashboard API Views
Real-time monitoring and management endpoints
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from app1.dashboard_service import AdminDashboardService
import logging

logger = logging.getLogger(__name__)


class DashboardOverviewView(APIView):
    """Main dashboard overview"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get dashboard overview with all key metrics"""
        overview = AdminDashboardService.get_dashboard_overview()
        return Response(overview, status=status.HTTP_200_OK)


class ActiveSessionsView(APIView):
    """Currently active check-ins"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get students currently checked in"""
        sessions = AdminDashboardService.get_active_sessions()
        return Response({
            'active_sessions': sessions,
            'count': len(sessions)
        }, status=status.HTTP_200_OK)


class RecentActivitiesView(APIView):
    """Recent attendance activities feed"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get recent attendance activities"""
        limit = int(request.query_params.get('limit', 20))
        activities = AdminDashboardService.get_recent_activities(limit)
        return Response({
            'activities': activities,
            'count': len(activities)
        }, status=status.HTTP_200_OK)


class PendingActionsView(APIView):
    """Admin pending actions and tasks"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get pending admin actions"""
        actions = AdminDashboardService.get_pending_actions()
        return Response({
            'pending_actions': actions,
            'count': len(actions),
            'high_priority_count': sum(1 for a in actions if a.get('priority') == 'high')
        }, status=status.HTTP_200_OK)


class KeyPerformanceIndicatorsView(APIView):
    """Dashboard KPIs"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get key performance indicators"""
        kpis = AdminDashboardService.get_key_performance_indicators()
        return Response(kpis, status=status.HTTP_200_OK)


class AdminAlertsView(APIView):
    """System alerts for admin"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get critical alerts"""
        alerts = AdminDashboardService.get_admin_alerts()
        return Response({
            'alerts': alerts,
            'count': len(alerts),
            'critical_count': sum(1 for a in alerts if a.get('severity') == 'high')
        }, status=status.HTTP_200_OK)


class CompleteDashboardView(APIView):
    """Complete unified dashboard data"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Get complete dashboard with all sections"""
        dashboard_data = {
            'overview': AdminDashboardService.get_dashboard_overview(),
            'active_sessions': AdminDashboardService.get_active_sessions(),
            'recent_activities': AdminDashboardService.get_recent_activities(10),
            'pending_actions': AdminDashboardService.get_pending_actions(),
            'kpis': AdminDashboardService.get_key_performance_indicators()['kpi'],
            'alerts': AdminDashboardService.get_admin_alerts()
        }
        return Response(dashboard_data, status=status.HTTP_200_OK)
