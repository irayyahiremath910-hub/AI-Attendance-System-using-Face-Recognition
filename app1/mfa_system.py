"""
Multi-factor authentication system
Implements 2FA/MFA with OTP, email verification, and device management
"""

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import pyotp
import secrets
import qrcode
import logging
from io import BytesIO
import base64

logger = logging.getLogger(__name__)


class MFAModel:
    """Data models for MFA"""

    def __init__(self, user):
        self.user = user
        self.secret_key = None
        self.backup_codes = []
        self.devices = []
        self.sessions = {}


class OTPService:
    """Service for managing One-Time Passwords"""

    @staticmethod
    def generate_secret():
        """Generate TOTP secret key"""
        return pyotp.random_base32()

    @staticmethod
    def get_totp(secret):
        """Get TOTP instance"""
        return pyotp.TOTP(secret)

    @staticmethod
    def verify_otp(secret, otp_code):
        """Verify OTP code"""
        try:
            totp = pyotp.TOTP(secret)
            # Allow for time drift (±30 seconds)
            return totp.verify(otp_code, valid_window=1)
        except Exception as e:
            logger.error(f"OTP verification error: {str(e)}")
            return False

    @staticmethod
    def get_qr_code(user_email, secret, issuer="AI Attendance System"):
        """Generate QR code for authenticator app"""
        try:
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(
                name=user_email,
                issuer_name=issuer
            )

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            return qr_code_base64

        except Exception as e:
            logger.error(f"QR code generation error: {str(e)}")
            return None


class EmailOTPService:
    """Service for email-based OTP"""

    OTP_VALIDITY = 5  # minutes

    @staticmethod
    def generate_email_otp():
        """Generate 6-digit OTP for email"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    @staticmethod
    def create_otp_session(user_id, otp_code):
        """Create OTP session"""
        return {
            'user_id': user_id,
            'otp': otp_code,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=EmailOTPService.OTP_VALIDITY),
            'attempts': 0,
        }

    @staticmethod
    def verify_email_otp(session, otp_code, max_attempts=3):
        """Verify email OTP with rate limiting"""
        if session['attempts'] >= max_attempts:
            return False, "Maximum attempts exceeded"

        if datetime.now() > session['expires_at']:
            return False, "OTP expired"

        session['attempts'] += 1

        if session['otp'] == otp_code:
            return True, "OTP verified"

        return False, f"Invalid OTP ({max_attempts - session['attempts']} attempts remaining)"


class BackupCodeService:
    """Service for backup codes"""

    @staticmethod
    def generate_backup_codes(count=10):
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = '-'.join([
                ''.join([secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') 
                        for _ in range(4)])
                for _ in range(2)
            ])
            codes.append(code)
        return codes

    @staticmethod
    def verify_backup_code(code, backup_codes):
        """Verify and consume backup code"""
        if code in backup_codes:
            backup_codes.remove(code)
            return True
        return False


class DeviceManagement:
    """Manage trusted devices"""

    @staticmethod
    def generate_device_id():
        """Generate unique device ID"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def register_device(user_id, device_name, device_type):
        """Register trusted device"""
        return {
            'device_id': DeviceManagement.generate_device_id(),
            'user_id': user_id,
            'device_name': device_name,
            'device_type': device_type,  # 'mobile', 'laptop', etc.
            'registered_at': datetime.now(),
            'last_used': datetime.now(),
            'is_active': True,
        }

    @staticmethod
    def verify_device(device_id, registered_devices):
        """Check if device is trusted"""
        for device in registered_devices:
            if device['device_id'] == device_id and device['is_active']:
                device['last_used'] = datetime.now()
                return True
        return False


class MFAManager:
    """Core MFA management service"""

    def __init__(self, user):
        self.user = user
        self.totp_secret = None
        self.backup_codes = []
        self.registered_devices = []
        self.mfa_enabled = False

    def enable_totp(self):
        """Enable TOTP authentication"""
        try:
            self.totp_secret = OTPService.generate_secret()
            qr_code = OTPService.get_qr_code(self.user.email, self.totp_secret)
            self.backup_codes = BackupCodeService.generate_backup_codes()

            logger.info(f"TOTP enabled for user {self.user.id}")
            return {
                'secret': self.totp_secret,
                'qr_code': qr_code,
                'backup_codes': self.backup_codes,
            }
        except Exception as e:
            logger.error(f"Error enabling TOTP: {str(e)}")
            return None

    def verify_totp_setup(self, otp_code):
        """Verify TOTP setup with test OTP"""
        if OTPService.verify_otp(self.totp_secret, otp_code):
            self.mfa_enabled = True
            logger.info(f"TOTP verified for user {self.user.id}")
            return True
        return False

    def disable_totp(self):
        """Disable TOTP authentication"""
        self.totp_secret = None
        self.mfa_enabled = False
        logger.info(f"TOTP disabled for user {self.user.id}")

    def register_trusted_device(self, device_name, device_type):
        """Register a trusted device"""
        device = DeviceManagement.register_device(
            self.user.id,
            device_name,
            device_type
        )
        self.registered_devices.append(device)
        logger.info(f"Device registered for user {self.user.id}: {device_name}")
        return device

    def is_device_trusted(self, device_id):
        """Check if device is trusted"""
        return DeviceManagement.verify_device(device_id, self.registered_devices)

    def get_trusted_devices(self):
        """Get list of trusted devices"""
        return [
            {
                'device_id': d['device_id'],
                'device_name': d['device_name'],
                'device_type': d['device_type'],
                'registered_at': d['registered_at'].isoformat(),
                'last_used': d['last_used'].isoformat(),
            }
            for d in self.registered_devices
        ]

    def revoke_device(self, device_id):
        """Revoke a trusted device"""
        for device in self.registered_devices:
            if device['device_id'] == device_id:
                device['is_active'] = False
                logger.info(f"Device revoked for user {self.user.id}: {device_id}")
                return True
        return False

    def use_backup_code(self, code):
        """Use backup code for authentication"""
        if BackupCodeService.verify_backup_code(code, self.backup_codes):
            logger.info(f"Backup code used for user {self.user.id}")
            return True
        logger.warning(f"Invalid backup code attempt for user {self.user.id}")
        return False

    def regenerate_backup_codes(self):
        """Regenerate backup codes"""
        self.backup_codes = BackupCodeService.generate_backup_codes()
        logger.info(f"Backup codes regenerated for user {self.user.id}")
        return self.backup_codes

    def get_mfa_status(self):
        """Get MFA status for user"""
        return {
            'user_id': self.user.id,
            'username': self.user.username,
            'mfa_enabled': self.mfa_enabled,
            'totp_configured': self.totp_secret is not None,
            'backup_codes_available': len(self.backup_codes),
            'trusted_devices_count': len([d for d in self.registered_devices if d['is_active']]),
            'devices': self.get_trusted_devices(),
        }


class MFAMiddleware:
    """Middleware for enforcing MFA"""

    def __init__(self, user, request_data):
        self.user = user
        self.request_data = request_data
        self.mfa_manager = MFAManager(user)

    def require_mfa(self):
        """Check if MFA is required"""
        return self.mfa_manager.mfa_enabled

    def verify_mfa(self, otp_code=None, device_id=None, backup_code=None):
        """Verify MFA credentials"""
        if otp_code:
            return OTPService.verify_otp(
                self.mfa_manager.totp_secret,
                otp_code
            )

        if device_id:
            return self.mfa_manager.is_device_trusted(device_id)

        if backup_code:
            return self.mfa_manager.use_backup_code(backup_code)

        return False

    def create_mfa_session(self):
        """Create MFA challenge session"""
        return {
            'user_id': self.user.id,
            'challenge_id': secrets.token_urlsafe(32),
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=10),
            'verified': False,
        }


class RecoveryCodeService:
    """Manage recovery codes for account recovery"""

    @staticmethod
    def generate_recovery_codes(count=5):
        """Generate recovery codes"""
        codes = []
        for _ in range(count):
            code = secrets.token_urlsafe(16)
            codes.append(code)
        return codes

    @staticmethod
    def create_recovery_account(user_id, recovery_codes, backup_email):
        """Create recovery account info"""
        return {
            'user_id': user_id,
            'recovery_codes': recovery_codes,
            'backup_email': backup_email,
            'created_at': datetime.now(),
            'last_recovery_at': None,
        }
