"""WebSocket Consumers for Real-time Updates - Day 9

This module implements WebSocket consumers for real-time attendance updates,
admin notifications, and live monitoring capabilities.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from app1.models import Student, Attendance

logger = logging.getLogger(__name__)


class AttendanceUpdateConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time attendance updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        self.room_name = f"user_{self.user.id}"
        self.room_group_name = f"attendance_{self.room_name}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.username} connected to attendance updates")
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to attendance updates',
            'timestamp': timezone.now().isoformat(),
            'user': self.user.username
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user.username} disconnected from attendance updates")
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_student':
                student_id = data.get('student_id')
                await self.subscribe_to_student(student_id)
            elif message_type == 'unsubscribe_student':
                student_id = data.get('student_id')
                await self.unsubscribe_from_student(student_id)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
    
    async def subscribe_to_student(self, student_id):
        """Subscribe to a specific student's attendance updates."""
        # Verify user has permission to subscribe
        has_permission = await self.check_student_permission(student_id)
        
        if has_permission:
            student_room = f"student_{student_id}"
            await self.channel_layer.group_add(
                student_room,
                self.channel_name
            )
            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'student_id': student_id,
                'message': 'Subscribed to student updates'
            }))
            logger.info(f"User {self.user.username} subscribed to student {student_id}")
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'detail': 'Permission denied'
            }))
    
    async def unsubscribe_from_student(self, student_id):
        """Unsubscribe from a student's attendance updates."""
        student_room = f"student_{student_id}"
        await self.channel_layer.group_discard(
            student_room,
            self.channel_name
        )
        logger.info(f"User {self.user.username} unsubscribed from student {student_id}")
    
    @database_sync_to_async
    def check_student_permission(self, student_id):
        """Check if user has permission to view student."""
        # Admin can see all students
        if self.user.is_staff:
            return True
        # User can only see themselves
        if hasattr(self.user, 'student'):
            return self.user.student.id == student_id
        return False
    
    async def attendance_update(self, event):
        """Handle attendance update message."""
        await self.send(text_data=json.dumps({
            'type': 'attendance_update',
            'student_id': event['student_id'],
            'student_name': event['student_name'],
            'status': event['status'],
            'time': event['time'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def check_in_notification(self, event):
        """Handle check-in notification."""
        await self.send(text_data=json.dumps({
            'type': 'check_in',
            'student_id': event['student_id'],
            'student_name': event['student_name'],
            'check_in_time': event['check_in_time'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def check_out_notification(self, event):
        """Handle check-out notification."""
        await self.send(text_data=json.dumps({
            'type': 'check_out',
            'student_id': event['student_id'],
            'student_name': event['student_name'],
            'check_out_time': event['check_out_time'],
            'duration': event.get('duration'),
            'timestamp': timezone.now().isoformat()
        }))


class AdminDashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for admin dashboard real-time updates."""
    
    async def connect(self):
        """Handle WebSocket connection for admin."""
        self.user = self.scope["user"]
        
        # Check if user is admin
        if not self.user.is_staff:
            await self.close()
            logger.warning(f"Non-admin user {self.user.username} attempted admin dashboard access")
            return
        
        self.room_group_name = "admin_dashboard"
        
        # Join admin group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Admin {self.user.username} connected to dashboard")
        
        # Send initial dashboard state
        await self.send_dashboard_state()
    
    async def disconnect(self, close_code):
        """Handle disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Admin {self.user.username} disconnected from dashboard")
    
    async def send_dashboard_state(self):
        """Send current dashboard state."""
        stats = await self.get_dashboard_stats()
        
        await self.send(text_data=json.dumps({
            'type': 'dashboard_state',
            'stats': stats,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_dashboard_stats(self):
        """Get current dashboard statistics."""
        total_students = Student.objects.count()
        authorized = Student.objects.filter(authorized=True).count()
        
        today = timezone.now().date()
        today_present = Attendance.objects.filter(
            date=today,
            check_in_time__isnull=False
        ).count()
        
        pending_checkout = Attendance.objects.filter(
            date=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).count()
        
        return {
            'total_students': total_students,
            'authorized': authorized,
            'today_present': today_present,
            'pending_checkout': pending_checkout,
            'authorization_rate': round((authorized / total_students * 100) if total_students > 0 else 0, 2)
        }
    
    async def receive(self, text_data):
        """Receive message from admin."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'refresh_stats':
                await self.send_dashboard_state()
            elif message_type == 'request_alerts':
                alerts = await self.get_pending_alerts()
                await self.send(text_data=json.dumps({
                    'type': 'alerts',
                    'alerts': alerts
                }))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in admin message")
    
    async def dashboard_update(self, event):
        """Handle dashboard update message."""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'event': event['event'],
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def alert_notification(self, event):
        """Handle alert notification."""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'severity': event['severity'],
            'message': event['message'],
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_pending_alerts(self):
        """Get pending alerts for admin."""
        alerts = []
        
        # Check for unauthorized students without face encoding
        unauthorized_no_face = Student.objects.filter(
            authorized=False
        ).count()
        
        if unauthorized_no_face > 0:
            alerts.append({
                'type': 'unauthorized_students',
                'count': unauthorized_no_face,
                'message': f'{unauthorized_no_face} students need authorization'
            })
        
        # Check for students not checked out
        pending_checkout = Attendance.objects.filter(
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).count()
        
        if pending_checkout > 0:
            alerts.append({
                'type': 'pending_checkout',
                'count': pending_checkout,
                'message': f'{pending_checkout} students pending checkout'
            })
        
        return alerts


class NotificationConsumer(WebsocketConsumer):
    """Synchronous WebSocket consumer for notifications (fallback)."""
    
    def connect(self):
        """Accept WebSocket connection."""
        self.user = self.scope["user"]
        self.accept()
        logger.info(f"User {self.user.username} connected to notifications")
    
    def disconnect(self, close_code):
        """Handle disconnection."""
        logger.info(f"User {self.user.username} disconnected from notifications")
    
    def receive(self, text_data):
        """Handle incoming message."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Echo received message
            self.send(text_data=json.dumps({
                'type': 'notification_received',
                'original_type': message_type,
                'timestamp': timezone.now().isoformat()
            }))
        except json.JSONDecodeError:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))


logger.info("WebSocket consumers initialized")
