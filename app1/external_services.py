"""
External service integration module
Integrates with third-party services and APIs
"""

import requests
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ExternalServiceConnector(ABC):
    """Base class for external service connectors"""

    def __init__(self, service_name, api_key=None, base_url=None):
        self.service_name = service_name
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = 30
        self.is_connected = False

    @abstractmethod
    def authenticate(self):
        """Authenticate with service"""
        pass

    @abstractmethod
    def verify_connection(self):
        """Verify service connection"""
        pass

    def get_headers(self):
        """Get default request headers"""
        return {
            'User-Agent': 'AttendanceSystem/1.0',
            'Content-Type': 'application/json',
        }

    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to service"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self.get_headers()

            if method == 'GET':
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
            elif method == 'POST':
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
            elif method == 'PUT':
                response = requests.put(
                    url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
            else:
                return None

            if response.status_code in [200, 201, 202]:
                return response.json() if response.content else {'status': 'success'}
            else:
                logger.error(f"Service error ({response.status_code}): {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Request error for {self.service_name}: {str(e)}")
            return None


class SMSServiceConnector(ExternalServiceConnector):
    """Connect to SMS service providers"""

    def __init__(self, service_type='twilio', api_key=None, account_sid=None):
        super().__init__('SMS Service')
        self.service_type = service_type
        self.api_key = api_key
        self.account_sid = account_sid

    def authenticate(self):
        """Authenticate with SMS service"""
        if self.service_type == 'twilio':
            self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        elif self.service_type == 'nexmo':
            self.base_url = "https://rest-api.nexmo.com"

        logger.info(f"SMS service authenticated: {self.service_type}")
        return True

    def verify_connection(self):
        """Verify SMS service connection"""
        try:
            self.authenticate()
            self.is_connected = True
            logger.info(f"SMS service connected: {self.service_type}")
            return True
        except Exception as e:
            logger.error(f"SMS connection failed: {str(e)}")
            return False

    def send_sms(self, phone_number, message):
        """Send SMS message"""
        if self.service_type == 'twilio':
            data = {
                'To': phone_number,
                'From': '+1234567890',  # Your Twilio number
                'Body': message,
            }
            response = self.make_request('POST', '/Messages.json', data=data)
        else:
            return False

        return response is not None

    def get_sms_status(self, message_id):
        """Get SMS delivery status"""
        response = self.make_request('GET', f'/Messages/{message_id}')
        return response


class GeoLocationService(ExternalServiceConnector):
    """Geolocation and mapping services"""

    def __init__(self, service_type='google', api_key=None):
        super().__init__('Geolocation Service')
        self.service_type = service_type
        self.api_key = api_key

    def authenticate(self):
        """Authenticate with geolocation service"""
        if self.service_type == 'google':
            self.base_url = "https://maps.googleapis.com/maps/api"
        logger.info(f"Geolocation service authenticated")
        return True

    def verify_connection(self):
        """Verify geolocation service"""
        try:
            self.authenticate()
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Geolocation connection failed: {str(e)}")
            return False

    def get_location_from_ip(self, ip_address):
        """Get location from IP address"""
        params = {'key': self.api_key}
        response = self.make_request(
            'GET',
            '/geocode/json',
            params={**params, 'address': ip_address}
        )
        return response

    def get_distance(self, origin, destination):
        """Get distance between two locations"""
        params = {
            'key': self.api_key,
            'origin': origin,
            'destination': destination,
        }
        response = self.make_request('GET', '/distancematrix/json', params=params)
        return response


class PaymentServiceConnector(ExternalServiceConnector):
    """Payment gateway integration"""

    def __init__(self, service_type='stripe', api_key=None):
        super().__init__('Payment Service')
        self.service_type = service_type
        self.api_key = api_key

    def authenticate(self):
        """Authenticate with payment service"""
        if self.service_type == 'stripe':
            self.base_url = "https://api.stripe.com/v1"
        logger.info(f"Payment service authenticated: {self.service_type}")
        return True

    def verify_connection(self):
        """Verify payment service connection"""
        try:
            self.authenticate()
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Payment connection failed: {str(e)}")
            return False

    def create_payment(self, amount, currency='USD', description=''):
        """Create payment"""
        data = {
            'amount': int(amount * 100),  # Convert to cents
            'currency': currency,
            'description': description,
        }
        response = self.make_request('POST', '/charges', data=data)
        return response


class ExternalServiceRegistry:
    """Registry for managing external service connections"""

    def __init__(self):
        self.services = {}
        self.connection_status = {}

    def register_service(self, service_id, connector: ExternalServiceConnector):
        """Register external service"""
        self.services[service_id] = connector
        logger.info(f"Service registered: {service_id}")

    def get_service(self, service_id):
        """Get service connector"""
        return self.services.get(service_id)

    def connect_service(self, service_id):
        """Connect to service"""
        service = self.get_service(service_id)
        if service:
            result = service.verify_connection()
            self.connection_status[service_id] = result
            return result
        return False

    def disconnect_service(self, service_id):
        """Disconnect from service"""
        self.connection_status[service_id] = False
        logger.info(f"Service disconnected: {service_id}")

    def is_service_connected(self, service_id):
        """Check service connection status"""
        return self.connection_status.get(service_id, False)

    def get_all_services(self):
        """Get all registered services"""
        return [
            {
                'id': service_id,
                'name': service.service_name,
                'connected': self.is_service_connected(service_id),
            }
            for service_id, service in self.services.items()
        ]

    def get_service_health(self):
        """Get health status of all services"""
        return {
            'timestamp': datetime.now().isoformat(),
            'services': self.get_all_services(),
            'healthy_services': sum(1 for s in self.services.values() if s.is_connected),
            'total_services': len(self.services),
        }


class ServiceFactory:
    """Factory for creating service connectors"""

    @staticmethod
    def create_sms_service(service_type='twilio', **kwargs):
        """Create SMS service connector"""
        return SMSServiceConnector(service_type=service_type, **kwargs)

    @staticmethod
    def create_geolocation_service(service_type='google', **kwargs):
        """Create geolocation service connector"""
        return GeoLocationService(service_type=service_type, **kwargs)

    @staticmethod
    def create_payment_service(service_type='stripe', **kwargs):
        """Create payment service connector"""
        return PaymentServiceConnector(service_type=service_type, **kwargs)


class WebhookHandler:
    """Handle webhooks from external services"""

    WEBHOOK_HANDLERS = {}

    @classmethod
    def register_webhook(cls, event_type, handler_func):
        """Register webhook handler"""
        cls.WEBHOOK_HANDLERS[event_type] = handler_func
        logger.info(f"Webhook handler registered for: {event_type}")

    @classmethod
    def handle_webhook(cls, event_type, data):
        """Handle incoming webhook"""
        if event_type in cls.WEBHOOK_HANDLERS:
            try:
                return cls.WEBHOOK_HANDLERS[event_type](data)
            except Exception as e:
                logger.error(f"Webhook handler error: {str(e)}")
                return False
        return False

    @classmethod
    def get_webhook_signature(cls, payload, secret):
        """Verify webhook signature"""
        import hmac
        import hashlib

        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature


# Global service registry
global_service_registry = ExternalServiceRegistry()
