"""Real-time Notification Service - Day 9

This module provides services for sending real-time notifications via WebSocket
for attendance events, alerts, and dashboard updates.
"""

from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from app1.ws_routing import WebSocketEventHandler, WebSocketChannelLayer
import logging
import json

logger = logging.getLogger(__name__)


class RealtimeNotificationService:
    """Service for managing real-time notifications."""
    
    # Cache keys
    RECENT_EVENTS_CACHE = "recent_events"
    ACTIVE_SESSIONS_CACHE = "active_sessions"
    NOTIFICATION_QUEUE = "notification_queue"
    
    @staticmethod
    def notify_attendance_check_in(channel_layer, student, check_in_time):
        """Notify about student check-in."""
        try:
            WebSocketEventHandler.send_check_in_notification(
                channel_layer,
                student.id,
                student.name,
                check_in_time
            )
            
            # Cache the event
            RealtimeNotificationService.cache_event({
                'type': 'check_in',
                'student_id': student.id,
                'student_name': student.name,
                'time': check_in_time.isoformat() if hasattr(check_in_time, 'isoformat') else str(check_in_time),
                'timestamp': timezone.now().isoformat()
            })
            
            logger.info(f"Check-in notification sent for {student.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send check-in notification: {str(e)}")
            return False
    
    @staticmethod
    def notify_attendance_check_out(channel_layer, student, check_out_time, attendance):
        """Notify about student check-out."""
        try:
            duration = None
            if attendance.check_in_time and attendance.check_out_time:
                duration = (attendance.check_out_time - attendance.check_in_time).total_seconds() / 3600
            
            WebSocketEventHandler.send_check_out_notification(
                channel_layer,
                student.id,
                student.name,
                check_out_time,
                duration=duration
            )
            
            # Cache the event
            RealtimeNotificationService.cache_event({
                'type': 'check_out',
                'student_id': student.id,
                'student_name': student.name,
                'time': check_out_time.isoformat() if hasattr(check_out_time, 'isoformat') else str(check_out_time),
                'duration_hours': round(duration, 2) if duration else None,
                'timestamp': timezone.now().isoformat()
            })
            
            logger.info(f"Check-out notification sent for {student.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send check-out notification: {str(e)}")
            return False
    
    @staticmethod
    def notify_admin_alert(channel_layer, severity, message, data=None):
        """Send alert to admin dashboard."""
        try:
            WebSocketEventHandler.send_admin_alert(channel_layer, severity, message)
            
            # Cache the alert
            alert = {
                'type': 'admin_alert',
                'severity': severity,
                'message': message,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            RealtimeNotificationService.cache_event(alert)
            logger.warning(f"Admin alert [{severity}]: {message}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send admin alert: {str(e)}")
            return False
    
    @staticmethod
    def notify_dashboard_update(channel_layer, event_type, data):
        """Notify admin dashboard of updates."""
        try:
            from asgiref.sync import async_to_sync
            
            group_name = WebSocketChannelLayer.get_admin_group()
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'dashboard_update',
                    'event': event_type,
                    'data': data,
                }
            )
            
            logger.info(f"Dashboard update sent: {event_type}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send dashboard update: {str(e)}")
            return False
    
    @staticmethod
    def cache_event(event):
        """Cache an event for retrieval by WebSocket clients."""
        try:
            events = cache.get(RealtimeNotificationService.RECENT_EVENTS_CACHE, [])
            events.append(event)
            
            # Keep only last 100 events
            if len(events) > 100:
                events = events[-100:]
            
            cache.set(RealtimeNotificationService.RECENT_EVENTS_CACHE, events, timeout=3600)
            return True
        
        except Exception as e:
            logger.error(f"Failed to cache event: {str(e)}")
            return False
    
    @staticmethod
    def get_recent_events(limit=20):
        """Get recent events from cache."""
        try:
            events = cache.get(RealtimeNotificationService.RECENT_EVENTS_CACHE, [])
            return events[-limit:]
        
        except Exception as e:
            logger.error(f"Failed to retrieve recent events: {str(e)}")
            return []
    
    @staticmethod
    def register_active_session(user_id, session_info):
        """Register an active WebSocket session."""
        try:
            sessions = cache.get(RealtimeNotificationService.ACTIVE_SESSIONS_CACHE, {})
            sessions[str(user_id)] = {
                'user_id': user_id,
                'connected_at': timezone.now().isoformat(),
                'info': session_info
            }
            cache.set(RealtimeNotificationService.ACTIVE_SESSIONS_CACHE, sessions, timeout=86400)
            return True
        
        except Exception as e:
            logger.error(f"Failed to register session: {str(e)}")
            return False
    
    @staticmethod
    def unregister_active_session(user_id):
        """Unregister an active WebSocket session."""
        try:
            sessions = cache.get(RealtimeNotificationService.ACTIVE_SESSIONS_CACHE, {})
            if str(user_id) in sessions:
                del sessions[str(user_id)]
            cache.set(RealtimeNotificationService.ACTIVE_SESSIONS_CACHE, sessions, timeout=86400)
            return True
        
        except Exception as e:
            logger.error(f"Failed to unregister session: {str(e)}")
            return False
    
    @staticmethod
    def get_active_sessions():
        """Get all active WebSocket sessions."""
        try:
            return cache.get(RealtimeNotificationService.ACTIVE_SESSIONS_CACHE, {})
        
        except Exception as e:
            logger.error(f"Failed to retrieve active sessions: {str(e)}")
            return {}
    
    @staticmethod
    def get_active_user_count():
        """Get count of active WebSocket sessions."""
        return len(RealtimeNotificationService.get_active_sessions())


class NotificationQueue:
    """Queue for managing pending notifications."""
    
    @staticmethod
    def enqueue_notification(notification_type, recipient_id, data):
        """Add notification to queue."""
        try:
            queue = cache.get(RealtimeNotificationService.NOTIFICATION_QUEUE, [])
            notification = {
                'type': notification_type,
                'recipient_id': recipient_id,
                'data': data,
                'queued_at': timezone.now().isoformat(),
                'status': 'pending'
            }
            queue.append(notification)
            cache.set(RealtimeNotificationService.NOTIFICATION_QUEUE, queue, timeout=3600)
            return True
        
        except Exception as e:
            logger.error(f"Failed to enqueue notification: {str(e)}")
            return False
    
    @staticmethod
    def dequeue_notifications(recipient_id, limit=10):
        """Get pending notifications for a recipient."""
        try:
            queue = cache.get(RealtimeNotificationService.NOTIFICATION_QUEUE, [])
            user_notifications = [
                n for n in queue 
                if n['recipient_id'] == recipient_id and n['status'] == 'pending'
            ]
            return user_notifications[:limit]
        
        except Exception as e:
            logger.error(f"Failed to dequeue notifications: {str(e)}")
            return []
    
    @staticmethod
    def mark_as_delivered(notification_id):
        """Mark a notification as delivered."""
        try:
            queue = cache.get(RealtimeNotificationService.NOTIFICATION_QUEUE, [])
            for notification in queue:
                if notification.get('id') == notification_id:
                    notification['status'] = 'delivered'
                    notification['delivered_at'] = timezone.now().isoformat()
            cache.set(RealtimeNotificationService.NOTIFICATION_QUEUE, queue, timeout=3600)
            return True
        
        except Exception as e:
            logger.error(f"Failed to mark notification as delivered: {str(e)}")
            return False


class NotificationAnalytics:
    """Track and analyze notification metrics."""
    
    METRICS_CACHE = "notification_metrics"
    
    @staticmethod
    def track_notification(notification_type, success=True):
        """Track a notification event."""
        try:
            metrics = cache.get(NotificationAnalytics.METRICS_CACHE, {})
            
            if notification_type not in metrics:
                metrics[notification_type] = {
                    'sent': 0,
                    'failed': 0,
                    'last_sent': None
                }
            
            if success:
                metrics[notification_type]['sent'] += 1
            else:
                metrics[notification_type]['failed'] += 1
            
            metrics[notification_type]['last_sent'] = timezone.now().isoformat()
            
            cache.set(NotificationAnalytics.METRICS_CACHE, metrics, timeout=86400)
            return True
        
        except Exception as e:
            logger.error(f"Failed to track notification: {str(e)}")
            return False
    
    @staticmethod
    def get_metrics():
        """Get notification metrics."""
        try:
            return cache.get(NotificationAnalytics.METRICS_CACHE, {})
        
        except Exception as e:
            logger.error(f"Failed to retrieve metrics: {str(e)}")
            return {}
    
    @staticmethod
    def get_success_rate(notification_type):
        """Get success rate for a notification type."""
        metrics = NotificationAnalytics.get_metrics()
        
        if notification_type not in metrics:
            return 100.0
        
        m = metrics[notification_type]
        total = m['sent'] + m['failed']
        
        if total == 0:
            return 100.0
        
        return round((m['sent'] / total) * 100, 2)


logger.info("Real-time notification service initialized")
