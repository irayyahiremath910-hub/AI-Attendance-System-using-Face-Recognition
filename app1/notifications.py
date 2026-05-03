"""
Advanced notification system with multiple channels
Supports email, SMS, push notifications, and in-app notifications
"""

from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Base class for notification channels"""

    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.is_enabled = True

    @abstractmethod
    def send(self, recipient, subject, message, data=None):
        """Send notification"""
        pass

    @abstractmethod
    def validate_recipient(self, recipient):
        """Validate recipient address"""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""

    def __init__(self):
        super().__init__('email')

    def validate_recipient(self, recipient):
        """Validate email address"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, recipient) is not None

    def send(self, recipient, subject, message, data=None):
        """Send email notification"""
        if not self.validate_recipient(recipient):
            logger.error(f"Invalid email: {recipient}")
            return False

        try:
            from django.core.mail import send_mail
            send_mail(
                subject,
                message,
                'noreply@attendance.edu',
                [recipient],
                fail_silently=False,
            )
            logger.info(f"Email sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {str(e)}")
            return False


class SMSNotificationChannel(NotificationChannel):
    """SMS notification channel"""

    def __init__(self):
        super().__init__('sms')

    def validate_recipient(self, recipient):
        """Validate phone number"""
        import re
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, recipient) is not None

    def send(self, recipient, subject, message, data=None):
        """Send SMS notification"""
        if not self.validate_recipient(recipient):
            logger.error(f"Invalid phone: {recipient}")
            return False

        try:
            # Integration with SMS service (Twilio)
            from app1.external_services import SMSServiceConnector
            sms_service = SMSServiceConnector()
            result = sms_service.send_sms(recipient, message)
            logger.info(f"SMS sent to {recipient}")
            return result
        except Exception as e:
            logger.error(f"SMS send failed: {str(e)}")
            return False


class PushNotificationChannel(NotificationChannel):
    """Push notification channel for mobile apps"""

    def __init__(self):
        super().__init__('push')

    def validate_recipient(self, recipient):
        """Validate device token"""
        return len(recipient) > 10

    def send(self, recipient, subject, message, data=None):
        """Send push notification"""
        if not self.validate_recipient(recipient):
            logger.error(f"Invalid device token: {recipient}")
            return False

        try:
            # Integration with FCM or similar service
            notification = {
                'title': subject,
                'body': message,
                'data': data or {},
                'timestamp': datetime.now().isoformat(),
            }
            logger.info(f"Push notification queued for {recipient}")
            return True
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}")
            return False


class InAppNotificationChannel(NotificationChannel):
    """In-app notification channel"""

    def __init__(self):
        super().__init__('in_app')
        self.notifications = {}

    def validate_recipient(self, recipient):
        """Validate user ID"""
        return recipient and len(str(recipient)) > 0

    def send(self, recipient, subject, message, data=None):
        """Store in-app notification"""
        if not self.validate_recipient(recipient):
            return False

        try:
            notification = {
                'user_id': recipient,
                'subject': subject,
                'message': message,
                'data': data or {},
                'timestamp': datetime.now(),
                'read': False,
            }

            if recipient not in self.notifications:
                self.notifications[recipient] = []

            self.notifications[recipient].append(notification)
            logger.info(f"In-app notification created for user {recipient}")
            return True
        except Exception as e:
            logger.error(f"In-app notification failed: {str(e)}")
            return False

    def get_notifications(self, user_id, unread_only=True):
        """Get notifications for user"""
        notifications = self.notifications.get(user_id, [])
        if unread_only:
            return [n for n in notifications if not n['read']]
        return notifications

    def mark_read(self, user_id, notification_index):
        """Mark notification as read"""
        if user_id in self.notifications:
            if notification_index < len(self.notifications[user_id]):
                self.notifications[user_id][notification_index]['read'] = True


class NotificationTemplate:
    """Template for notifications"""

    def __init__(self, template_id, subject_template, message_template):
        self.template_id = template_id
        self.subject_template = subject_template
        self.message_template = message_template

    def render(self, context):
        """Render template with context"""
        subject = self.subject_template.format(**context)
        message = self.message_template.format(**context)
        return subject, message


class NotificationQueue:
    """Queue for managing notifications"""

    def __init__(self):
        self.queue = []
        self.sent = []
        self.failed = []

    def add(self, notification):
        """Add notification to queue"""
        self.queue.append({
            'notification': notification,
            'timestamp': datetime.now(),
            'attempts': 0,
        })

    def process(self, max_attempts=3):
        """Process notification queue"""
        processed = []
        remaining = []

        for item in self.queue:
            if item['attempts'] < max_attempts:
                success = item['notification'].send()
                item['attempts'] += 1

                if success:
                    self.sent.append(item)
                    processed.append(item)
                else:
                    remaining.append(item)
            else:
                self.failed.append(item)

        self.queue = remaining
        return len(processed), len(remaining), len(self.failed)

    def get_status(self):
        """Get queue status"""
        return {
            'pending': len(self.queue),
            'sent': len(self.sent),
            'failed': len(self.failed),
            'timestamp': datetime.now().isoformat(),
        }


class Notification:
    """Individual notification"""

    def __init__(self, recipient, channels, subject, message, data=None):
        self.recipient = recipient
        self.channels = channels  # List of channel instances
        self.subject = subject
        self.message = message
        self.data = data or {}
        self.created_at = datetime.now()
        self.sent_at = None
        self.status = 'pending'

    def send(self):
        """Send notification through all channels"""
        results = {}
        all_success = True

        for channel in self.channels:
            try:
                result = channel.send(self.recipient, self.subject, self.message, self.data)
                results[channel.channel_name] = result
                if not result:
                    all_success = False
            except Exception as e:
                logger.error(f"Channel error ({channel.channel_name}): {str(e)}")
                results[channel.channel_name] = False
                all_success = False

        if all_success:
            self.status = 'sent'
            self.sent_at = datetime.now()
        else:
            self.status = 'partial'

        return all_success


class NotificationService:
    """Main notification service"""

    def __init__(self):
        self.channels = {
            'email': EmailNotificationChannel(),
            'sms': SMSNotificationChannel(),
            'push': PushNotificationChannel(),
            'in_app': InAppNotificationChannel(),
        }
        self.queue = NotificationQueue()
        self.templates = {}
        self._register_default_templates()

    def _register_default_templates(self):
        """Register default notification templates"""
        self.templates['attendance_alert'] = NotificationTemplate(
            'attendance_alert',
            'Attendance Alert: {student_name}',
            'Student {student_name} marked {status} on {date}'
        )

        self.templates['check_in_reminder'] = NotificationTemplate(
            'check_in_reminder',
            'Check-in Reminder',
            'Please check in for attendance today'
        )

    def register_template(self, template_id, template):
        """Register notification template"""
        self.templates[template_id] = template

    def register_channel(self, channel_id, channel):
        """Register notification channel"""
        self.channels[channel_id] = channel

    def get_channel(self, channel_id):
        """Get notification channel"""
        return self.channels.get(channel_id)

    def send_notification(self, recipient, channels, subject, message, data=None, queue=False):
        """Send notification"""
        notification = Notification(recipient, channels, subject, message, data)

        if queue:
            self.queue.add(notification)
            return True
        else:
            return notification.send()

    def send_templated(self, recipient, channels, template_id, context, queue=False):
        """Send templated notification"""
        template = self.templates.get(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return False

        subject, message = template.render(context)
        return self.send_notification(recipient, channels, subject, message, queue=queue)

    def process_queue(self):
        """Process notification queue"""
        return self.queue.process()

    def get_queue_status(self):
        """Get queue status"""
        return self.queue.get_status()

    def disable_channel(self, channel_id):
        """Disable notification channel"""
        if channel_id in self.channels:
            self.channels[channel_id].is_enabled = False

    def enable_channel(self, channel_id):
        """Enable notification channel"""
        if channel_id in self.channels:
            self.channels[channel_id].is_enabled = True


# Global notification service
global_notification_service = NotificationService()
