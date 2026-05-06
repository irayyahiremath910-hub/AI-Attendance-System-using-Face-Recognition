"""
API rate limiting and quota management system
Protects against abuse, enforces usage limits, and manages API quotas
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Dict, Optional
import math

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""

    FIXED_WINDOW = 'fixed_window'
    SLIDING_WINDOW = 'sliding_window'
    TOKEN_BUCKET = 'token_bucket'
    LEAKY_BUCKET = 'leaky_bucket'


class QuotaType(Enum):
    """Quota types"""

    REQUESTS_PER_HOUR = 'requests_per_hour'
    REQUESTS_PER_DAY = 'requests_per_day'
    REQUESTS_PER_MONTH = 'requests_per_month'
    DATA_TRANSFER_PER_DAY = 'data_transfer_per_day'
    CONCURRENT_REQUESTS = 'concurrent_requests'


class RateLimiter:
    """Rate limiter using token bucket algorithm"""

    def __init__(self, rate_limit: int, window_seconds: int):
        self.rate_limit = rate_limit  # Number of tokens
        self.window_seconds = window_seconds
        self.tokens = rate_limit
        self.last_refill = datetime.now()

    def _refill_tokens(self):
        """Refill tokens based on time elapsed"""
        now = datetime.now()
        time_elapsed = (now - self.last_refill).total_seconds()
        
        tokens_to_add = (time_elapsed / self.window_seconds) * self.rate_limit
        self.tokens = min(self.rate_limit, self.tokens + tokens_to_add)
        self.last_refill = now

    def allow_request(self, tokens_needed=1):
        """Check if request is allowed"""
        self._refill_tokens()

        if self.tokens >= tokens_needed:
            self.tokens -= tokens_needed
            return True
        return False

    def get_status(self):
        """Get limiter status"""
        self._refill_tokens()
        return {
            'available_tokens': int(self.tokens),
            'max_tokens': self.rate_limit,
            'window_seconds': self.window_seconds,
            'last_refill': self.last_refill.isoformat(),
        }


class ClientQuota:
    """Quota for API client"""

    def __init__(self, client_id, quota_type: QuotaType, limit):
        self.client_id = client_id
        self.quota_type = quota_type
        self.limit = limit
        self.usage = 0
        self.reset_time = self._calculate_reset_time()
        self.created_at = datetime.now()
        self.is_exceeded = False

    def _calculate_reset_time(self):
        """Calculate quota reset time"""
        if self.quota_type == QuotaType.REQUESTS_PER_HOUR:
            return datetime.now() + timedelta(hours=1)
        elif self.quota_type == QuotaType.REQUESTS_PER_DAY:
            return datetime.now() + timedelta(days=1)
        elif self.quota_type == QuotaType.REQUESTS_PER_MONTH:
            return datetime.now() + timedelta(days=30)
        else:
            return datetime.now() + timedelta(hours=1)

    def increment_usage(self, amount=1):
        """Increment usage"""
        self.usage += amount
        if self.usage >= self.limit:
            self.is_exceeded = True

    def should_reset(self):
        """Check if quota should reset"""
        return datetime.now() >= self.reset_time

    def reset(self):
        """Reset quota"""
        self.usage = 0
        self.is_exceeded = False
        self.reset_time = self._calculate_reset_time()

    def get_remaining(self):
        """Get remaining quota"""
        return max(0, self.limit - self.usage)

    def get_status(self):
        """Get quota status"""
        return {
            'client_id': self.client_id,
            'quota_type': self.quota_type.value,
            'limit': self.limit,
            'usage': self.usage,
            'remaining': self.get_remaining(),
            'percentage_used': (self.usage / self.limit * 100) if self.limit > 0 else 0,
            'is_exceeded': self.is_exceeded,
            'reset_time': self.reset_time.isoformat(),
        }


class ApiKeyManager:
    """Manage API keys and client credentials"""

    def __init__(self):
        self.api_keys = {}
        self.key_quotas = {}

    def create_api_key(self, client_id, client_name, tier='standard'):
        """Create API key"""
        import secrets
        api_key = secrets.token_urlsafe(32)

        self.api_keys[api_key] = {
            'client_id': client_id,
            'client_name': client_name,
            'tier': tier,
            'created_at': datetime.now(),
            'is_active': True,
            'usage_count': 0,
        }

        logger.info(f"API key created for {client_name}")
        return api_key

    def validate_api_key(self, api_key):
        """Validate API key"""
        if api_key in self.api_keys:
            key_info = self.api_keys[api_key]
            if key_info['is_active']:
                return True, key_info
        return False, None

    def revoke_api_key(self, api_key):
        """Revoke API key"""
        if api_key in self.api_keys:
            self.api_keys[api_key]['is_active'] = False
            logger.info(f"API key revoked: {api_key}")
            return True
        return False

    def record_usage(self, api_key):
        """Record API key usage"""
        if api_key in self.api_keys:
            self.api_keys[api_key]['usage_count'] += 1

    def get_key_info(self, api_key):
        """Get API key information"""
        return self.api_keys.get(api_key)


class RateLimitPolicy:
    """Rate limit policy for endpoint"""

    def __init__(self, policy_id, endpoint, requests_per_minute=100, burst_limit=150):
        self.policy_id = policy_id
        self.endpoint = endpoint
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.strategy = RateLimitStrategy.TOKEN_BUCKET
        self.limiters = {}  # Per-client limiters
        self.created_at = datetime.now()

    def create_limiter(self, client_id):
        """Create limiter for client"""
        limiter = RateLimiter(
            rate_limit=self.requests_per_minute,
            window_seconds=60
        )
        self.limiters[client_id] = limiter
        return limiter

    def check_rate_limit(self, client_id):
        """Check rate limit for client"""
        if client_id not in self.limiters:
            self.create_limiter(client_id)

        limiter = self.limiters[client_id]
        return limiter.allow_request()

    def get_limiter_status(self, client_id):
        """Get limiter status"""
        if client_id in self.limiters:
            return self.limiters[client_id].get_status()
        return None

    def get_policy_info(self):
        """Get policy information"""
        return {
            'policy_id': self.policy_id,
            'endpoint': self.endpoint,
            'requests_per_minute': self.requests_per_minute,
            'burst_limit': self.burst_limit,
            'strategy': self.strategy.value,
            'active_clients': len(self.limiters),
            'created_at': self.created_at.isoformat(),
        }


class QuotaManager:
    """Manage client quotas"""

    def __init__(self):
        self.quotas: Dict[str, Dict] = {}
        self.quota_tiers = self._initialize_quota_tiers()

    def _initialize_quota_tiers(self):
        """Initialize default quota tiers"""
        return {
            'free': {
                QuotaType.REQUESTS_PER_DAY: 1000,
                QuotaType.DATA_TRANSFER_PER_DAY: 100 * 1024 * 1024,  # 100MB
            },
            'standard': {
                QuotaType.REQUESTS_PER_DAY: 100000,
                QuotaType.DATA_TRANSFER_PER_DAY: 10 * 1024 * 1024 * 1024,  # 10GB
            },
            'premium': {
                QuotaType.REQUESTS_PER_DAY: 1000000,
                QuotaType.DATA_TRANSFER_PER_DAY: 100 * 1024 * 1024 * 1024,  # 100GB
            },
        }

    def assign_quota(self, client_id, tier='standard'):
        """Assign quota tier to client"""
        if tier not in self.quota_tiers:
            tier = 'free'

        if client_id not in self.quotas:
            self.quotas[client_id] = {}

        tier_quotas = self.quota_tiers[tier]
        for quota_type, limit in tier_quotas.items():
            self.quotas[client_id][quota_type] = ClientQuota(client_id, quota_type, limit)

        logger.info(f"Quota assigned to {client_id}: {tier}")
        return self.quotas[client_id]

    def check_quota(self, client_id, quota_type: QuotaType):
        """Check if client has quota"""
        if client_id not in self.quotas:
            return False

        if quota_type not in self.quotas[client_id]:
            return False

        quota = self.quotas[client_id][quota_type]

        if quota.should_reset():
            quota.reset()

        return quota.get_remaining() > 0

    def consume_quota(self, client_id, quota_type: QuotaType, amount=1):
        """Consume quota"""
        if self.check_quota(client_id, quota_type):
            quota = self.quotas[client_id][quota_type]
            quota.increment_usage(amount)
            return True
        return False

    def get_client_quotas(self, client_id):
        """Get all quotas for client"""
        if client_id not in self.quotas:
            return None

        return {
            quota_type.value: quota.get_status()
            for quota_type, quota in self.quotas[client_id].items()
        }


class AbuseDetector:
    """Detect API abuse patterns"""

    def __init__(self):
        self.suspicious_activities = []
        self.abuse_threshold = 1000  # Requests in 1 minute

    def detect_abuse(self, client_id, request_count):
        """Detect potential abuse"""
        if request_count > self.abuse_threshold:
            abuse_event = {
                'client_id': client_id,
                'request_count': request_count,
                'detected_at': datetime.now(),
                'severity': 'high' if request_count > self.abuse_threshold * 2 else 'medium',
            }
            self.suspicious_activities.append(abuse_event)
            logger.warning(f"Potential abuse detected: {client_id}")
            return True
        return False

    def get_suspicious_activities(self, limit=50):
        """Get suspicious activities"""
        return self.suspicious_activities[-limit:]

    def block_client(self, client_id):
        """Block abusive client"""
        logger.error(f"Client blocked due to abuse: {client_id}")
        return True

    def get_abuse_report(self):
        """Get abuse report"""
        return {
            'total_suspicious_activities': len(self.suspicious_activities),
            'recent_activities': self.get_suspicious_activities(10),
            'high_severity_count': sum(1 for a in self.suspicious_activities if a['severity'] == 'high'),
        }


class ApiRateLimitManager:
    """Main API rate limiting manager"""

    def __init__(self):
        self.policies: Dict[str, RateLimitPolicy] = {}
        self.quota_manager = QuotaManager()
        self.api_key_manager = ApiKeyManager()
        self.abuse_detector = AbuseDetector()

    def create_policy(self, endpoint, requests_per_minute=100, burst_limit=150):
        """Create rate limit policy"""
        policy_id = f"policy_{endpoint}_{datetime.now().timestamp()}"
        policy = RateLimitPolicy(policy_id, endpoint, requests_per_minute, burst_limit)
        self.policies[endpoint] = policy
        logger.info(f"Rate limit policy created: {endpoint}")
        return policy

    def check_request(self, client_id, endpoint, api_key=None):
        """Check if request is allowed"""
        # Validate API key
        if api_key:
            is_valid, key_info = self.api_key_manager.validate_api_key(api_key)
            if not is_valid:
                return False, "Invalid API key"
            self.api_key_manager.record_usage(api_key)

        # Check endpoint rate limit
        if endpoint in self.policies:
            policy = self.policies[endpoint]
            if not policy.check_rate_limit(client_id):
                return False, "Rate limit exceeded"

        # Check quota
        if not self.quota_manager.check_quota(client_id, QuotaType.REQUESTS_PER_DAY):
            return False, "Daily quota exceeded"

        self.quota_manager.consume_quota(client_id, QuotaType.REQUESTS_PER_DAY)
        return True, "Allowed"

    def get_client_status(self, client_id):
        """Get client status and limits"""
        return {
            'client_id': client_id,
            'quotas': self.quota_manager.get_client_quotas(client_id),
            'abuse_detected': len([a for a in self.abuse_detector.suspicious_activities if a['client_id'] == client_id]) > 0,
        }

    def get_system_status(self):
        """Get system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'active_policies': len(self.policies),
            'managed_clients': len(self.quota_manager.quotas),
            'active_api_keys': sum(1 for k in self.api_key_manager.api_keys.values() if k['is_active']),
            'suspicious_activities': len(self.abuse_detector.suspicious_activities),
            'abuse_report': self.abuse_detector.get_abuse_report(),
        }

    def reset_client_quotas(self, client_id):
        """Force reset client quotas"""
        if client_id in self.quota_manager.quotas:
            for quota in self.quota_manager.quotas[client_id].values():
                quota.reset()
            logger.info(f"Quotas reset for client: {client_id}")
            return True
        return False


# Global rate limit manager
global_rate_limit_manager = ApiRateLimitManager()
