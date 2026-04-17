"""
WebSocket event broadcasting utility
Provides methods to broadcast events to connected WebSocket clients
"""

import asyncio
from channels.layers import get_channel_layer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebSocketBroadcaster:
    """Utility for broadcasting events to WebSocket groups"""

    @staticmethod
    def broadcast_attendance_event(student_id, student_name, action):
        """Broadcast attendance event (check-in/check-out)"""
        try:
            channel_layer = get_channel_layer()
            
            asyncio.run(channel_layer.group_send(
                'attendance_live',
                {
                    'type': 'attendance_update',
                    'student_id': student_id,
                    'student_name': student_name,
                    'action': action,  # 'check_in' or 'check_out'
                    'timestamp': datetime.now().isoformat()
                }
            ))
            logger.info(f"Broadcasted {action} event for student {student_id}")
        except Exception as e:
            logger.error(f"Error broadcasting attendance event: {str(e)}")

    @staticmethod
    def broadcast_dashboard_update(dashboard_data):
        """Broadcast dashboard update"""
        try:
            channel_layer = get_channel_layer()
            
            asyncio.run(channel_layer.group_send(
                'attendance_live',
                {
                    'type': 'dashboard_update',
                    'data': dashboard_data
                }
            ))
            logger.info("Broadcasted dashboard update")
        except Exception as e:
            logger.error(f"Error broadcasting dashboard update: {str(e)}")

    @staticmethod
    def broadcast_alert(severity, message):
        """Broadcast alert notification"""
        try:
            channel_layer = get_channel_layer()
            
            asyncio.run(channel_layer.group_send(
                'attendance_live',
                {
                    'type': 'alert_notification',
                    'severity': severity,  # 'high', 'medium', 'low'
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            ))
            logger.info(f"Broadcasted {severity} alert: {message}")
        except Exception as e:
            logger.error(f"Error broadcasting alert: {str(e)}")

    @staticmethod
    def broadcast_stats_update(metrics):
        """Broadcast statistics update"""
        try:
            channel_layer = get_channel_layer()
            
            asyncio.run(channel_layer.group_send(
                'attendance_stats',
                {
                    'type': 'stats_update',
                    'metrics': metrics,
                    'timestamp': datetime.now().isoformat()
                }
            ))
            logger.info("Broadcasted stats update")
        except Exception as e:
            logger.error(f"Error broadcasting stats: {str(e)}")

    @staticmethod
    def broadcast_face_recognition_event(student_id, student_name, confidence, camera_id=None):
        """Broadcast face recognition success event"""
        try:
            channel_layer = get_channel_layer()
            
            asyncio.run(channel_layer.group_send(
                'camera_control',
                {
                    'type': 'face_recognized',
                    'student_id': student_id,
                    'student_name': student_name,
                    'confidence': confidence,
                    'camera_id': camera_id,
                    'timestamp': datetime.now().isoformat()
                }
            ))
            logger.info(f"Broadcasted face recognition for student {student_id}")
        except Exception as e:
            logger.error(f"Error broadcasting face recognition: {str(e)}")

    @staticmethod
    def broadcast_face_recognition_failure(reason, camera_id=None):
        """Broadcast face recognition failure event"""
        try:
            channel_layer = get_channel_layer()
            
            asyncio.run(channel_layer.group_send(
                'camera_control',
                {
                    'type': 'face_recognition_failed',
                    'reason': reason,
                    'camera_id': camera_id,
                    'timestamp': datetime.now().isoformat()
                }
            ))
            logger.info(f"Broadcasted face recognition failure: {reason}")
        except Exception as e:
            logger.error(f"Error broadcasting failure: {str(e)}")

    @staticmethod
    def broadcast_camera_status(camera_id, status):
        """Broadcast camera status update"""
        try:
            channel_layer = get_channel_layer()
            
            asyncio.run(channel_layer.group_send(
                'camera_control',
                {
                    'type': 'camera_status_update',
                    'camera_id': camera_id,
                    'status': status,  # 'online', 'offline', 'error'
                    'timestamp': datetime.now().isoformat()
                }
            ))
            logger.info(f"Broadcasted camera {camera_id} status: {status}")
        except Exception as e:
            logger.error(f"Error broadcasting camera status: {str(e)}")
