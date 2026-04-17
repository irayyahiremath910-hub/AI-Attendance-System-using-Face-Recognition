"""
WebSocket consumers for real-time attendance updates
Provides live updates for dashboard and monitoring systems
"""

import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from app1.models import Student, Attendance, CameraConfiguration
from app1.dashboard_service import AdminDashboardService
from app1.analytics_service import AttendanceAnalyticsService

logger = logging.getLogger(__name__)


class AttendanceLiveConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live attendance updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_group_name = 'attendance_live'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}")
        
        # Send initial dashboard data
        dashboard_data = await self.get_initial_dashboard()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': dashboard_data
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data):
        """Handle received messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_dashboard':
                dashboard = await self.get_initial_dashboard()
                await self.send(text_data=json.dumps({
                    'type': 'dashboard_update',
                    'data': dashboard
                }))
            
            elif message_type == 'get_active_sessions':
                sessions = await self.get_active_sessions()
                await self.send(text_data=json.dumps({
                    'type': 'active_sessions',
                    'data': sessions
                }))
            
            elif message_type == 'get_alerts':
                alerts = await self.get_alerts()
                await self.send(text_data=json.dumps({
                    'type': 'alerts',
                    'data': alerts
                }))
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def attendance_update(self, event):
        """Receive attendance update from group"""
        await self.send(text_data=json.dumps({
            'type': 'attendance_update',
            'student_id': event['student_id'],
            'student_name': event['student_name'],
            'action': event['action'],  # 'check_in' or 'check_out'
            'timestamp': event['timestamp']
        }))

    async def dashboard_update(self, event):
        """Receive dashboard update from group"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }))

    async def alert_notification(self, event):
        """Receive alert notification"""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'severity': event['severity'],
            'message': event['message']
        }))

    @database_sync_to_async
    def get_initial_dashboard(self):
        """Get initial dashboard data"""
        try:
            overview = AdminDashboardService.get_dashboard_overview()
            kpis = AdminDashboardService.get_key_performance_indicators()
            alerts = AdminDashboardService.get_admin_alerts()
            pending = AdminDashboardService.get_pending_actions()
            
            return {
                'overview': overview,
                'kpis': kpis.get('kpi', []),
                'alerts': alerts,
                'pending_actions': pending,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard: {str(e)}")
            return {}

    @database_sync_to_async
    def get_active_sessions(self):
        """Get active check-in sessions"""
        try:
            return AdminDashboardService.get_active_sessions()
        except Exception as e:
            logger.error(f"Error getting active sessions: {str(e)}")
            return []

    @database_sync_to_async
    def get_alerts(self):
        """Get current alerts"""
        try:
            return AdminDashboardService.get_admin_alerts()
        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            return []


class AttendanceStatsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time statistics"""
    
    async def connect(self):
        """Handle connection"""
        self.room_group_name = 'attendance_stats'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Stats WebSocket connected: {self.channel_name}")

    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def stats_update(self, event):
        """Receive statistics update"""
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'metrics': event['metrics'],
            'timestamp': event['timestamp']
        }))

    async def receive(self, text_data):
        """Handle received messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_metrics':
                metrics = await self.get_metrics()
                await self.send(text_data=json.dumps({
                    'type': 'metrics',
                    'data': metrics
                }))
        except Exception as e:
            logger.error(f"Error in stats consumer: {str(e)}")

    @database_sync_to_async
    def get_metrics(self):
        """Get current metrics"""
        try:
            health = AttendanceAnalyticsService.get_system_health_metrics()
            kpis = AdminDashboardService.get_key_performance_indicators()
            return {
                'health': health,
                'kpis': kpis.get('kpi', []),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            return {}


class CameraControlConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for camera control and face recognition events"""
    
    async def connect(self):
        """Handle connection"""
        self.room_group_name = 'camera_control'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Camera control WebSocket connected: {self.channel_name}")

    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def face_recognized(self, event):
        """Receive face recognition event"""
        await self.send(text_data=json.dumps({
            'type': 'face_recognized',
            'student_id': event['student_id'],
            'student_name': event['student_name'],
            'confidence': event.get('confidence', 0.0),
            'timestamp': event['timestamp'],
            'camera_id': event.get('camera_id')
        }))

    async def face_recognition_failed(self, event):
        """Receive face recognition failure event"""
        await self.send(text_data=json.dumps({
            'type': 'face_recognition_failed',
            'reason': event['reason'],
            'timestamp': event['timestamp'],
            'camera_id': event.get('camera_id')
        }))

    async def camera_status_update(self, event):
        """Receive camera status update"""
        await self.send(text_data=json.dumps({
            'type': 'camera_status',
            'camera_id': event['camera_id'],
            'status': event['status'],  # 'online', 'offline', 'error'
            'timestamp': event['timestamp']
        }))
