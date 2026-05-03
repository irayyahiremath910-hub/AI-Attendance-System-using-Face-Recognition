"""
Comprehensive audit and compliance system
Tracks all system activities and ensures regulatory compliance
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import List, Dict
import json

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types"""

    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    DATA_ACCESS = 'data_access'
    DATA_MODIFY = 'data_modify'
    DATA_DELETE = 'data_delete'
    PERMISSION_CHANGE = 'permission_change'
    ROLE_CHANGE = 'role_change'
    SETTINGS_CHANGE = 'settings_change'
    REPORT_GENERATE = 'report_generate'
    EXPORT_DATA = 'export_data'
    SYSTEM_ERROR = 'system_error'
    SECURITY_EVENT = 'security_event'


class ComplianceStandard(Enum):
    """Compliance standards"""

    GDPR = 'gdpr'
    FERPA = 'ferpa'
    HIPAA = 'hipaa'
    SOC2 = 'soc2'
    ISO27001 = 'iso27001'


class AuditEvent:
    """Single audit event"""

    def __init__(self, event_type: AuditEventType, user_id, resource, action_details=None):
        self.event_id = self._generate_event_id()
        self.event_type = event_type
        self.user_id = user_id
        self.resource = resource
        self.action_details = action_details or {}
        self.timestamp = datetime.now()
        self.ip_address = None
        self.user_agent = None
        self.status = 'success'

    def _generate_event_id(self):
        """Generate unique event ID"""
        import uuid
        return str(uuid.uuid4())

    def set_context(self, ip_address, user_agent):
        """Set request context"""
        self.ip_address = ip_address
        self.user_agent = user_agent

    def get_info(self):
        """Get event information"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'resource': self.resource,
            'action_details': self.action_details,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
        }


class ComplianceCheck:
    """Compliance check"""

    def __init__(self, check_id, standard: ComplianceStandard, check_name, check_func):
        self.check_id = check_id
        self.standard = standard
        self.check_name = check_name
        self.check_func = check_func
        self.last_check = None
        self.status = 'not_checked'
        self.result = None

    def execute(self):
        """Execute compliance check"""
        try:
            self.result = self.check_func()
            self.status = 'passed' if self.result else 'failed'
            self.last_check = datetime.now()
            logger.info(f"Compliance check executed: {self.check_name} - {self.status}")
            return self.result
        except Exception as e:
            logger.error(f"Compliance check error ({self.check_name}): {str(e)}")
            self.status = 'error'
            return False

    def get_info(self):
        """Get check information"""
        return {
            'check_id': self.check_id,
            'standard': self.standard.value,
            'check_name': self.check_name,
            'status': self.status,
            'result': self.result,
            'last_check': self.last_check.isoformat() if self.last_check else None,
        }


class ComplianceReport:
    """Compliance report"""

    def __init__(self, report_id, standard: ComplianceStandard):
        self.report_id = report_id
        self.standard = standard
        self.checks_passed = 0
        self.checks_failed = 0
        self.check_results = []
        self.generated_at = datetime.now()
        self.compliance_score = 0.0

    def add_check_result(self, check: ComplianceCheck):
        """Add check result to report"""
        self.check_results.append(check.get_info())
        if check.status == 'passed':
            self.checks_passed += 1
        elif check.status == 'failed':
            self.checks_failed += 1

    def calculate_score(self):
        """Calculate compliance score"""
        total_checks = self.checks_passed + self.checks_failed
        if total_checks > 0:
            self.compliance_score = (self.checks_passed / total_checks) * 100
        return self.compliance_score

    def get_recommendations(self):
        """Get remediation recommendations"""
        recommendations = []
        for result in self.check_results:
            if result['status'] == 'failed':
                recommendations.append({
                    'check': result['check_name'],
                    'issue': f"Failed: {result['check_name']}",
                    'action': 'Review and remediate',
                })
        return recommendations

    def get_report(self):
        """Get full compliance report"""
        return {
            'report_id': self.report_id,
            'standard': self.standard.value,
            'generated_at': self.generated_at.isoformat(),
            'compliance_score': round(self.compliance_score, 2),
            'checks_passed': self.checks_passed,
            'checks_failed': self.checks_failed,
            'check_results': self.check_results,
            'recommendations': self.get_recommendations(),
        }


class DataRetentionPolicy:
    """Data retention policy"""

    def __init__(self, policy_id, description):
        self.policy_id = policy_id
        self.description = description
        self.retention_rules = {}
        self.created_at = datetime.now()

    def set_retention_period(self, data_type, days):
        """Set retention period for data type"""
        self.retention_rules[data_type] = {
            'days': days,
            'expiry_date': datetime.now() + timedelta(days=days),
        }

    def is_data_expired(self, data_type, created_date):
        """Check if data has expired"""
        if data_type in self.retention_rules:
            days = self.retention_rules[data_type]['days']
            expiry_date = created_date + timedelta(days=days)
            return datetime.now() > expiry_date
        return False

    def get_expired_records(self, records, data_type):
        """Get expired records"""
        expired = []
        for record in records:
            if self.is_data_expired(data_type, record.get('created_at')):
                expired.append(record)
        return expired


class ConsentManager:
    """Manage user consents and preferences"""

    def __init__(self):
        self.consents = {}

    def request_consent(self, user_id, consent_type, description):
        """Request user consent"""
        if user_id not in self.consents:
            self.consents[user_id] = {}

        self.consents[user_id][consent_type] = {
            'granted': False,
            'description': description,
            'requested_at': datetime.now(),
            'granted_at': None,
        }

    def grant_consent(self, user_id, consent_type):
        """Grant user consent"""
        if user_id in self.consents and consent_type in self.consents[user_id]:
            self.consents[user_id][consent_type]['granted'] = True
            self.consents[user_id][consent_type]['granted_at'] = datetime.now()
            logger.info(f"Consent granted: {user_id} - {consent_type}")
            return True
        return False

    def revoke_consent(self, user_id, consent_type):
        """Revoke user consent"""
        if user_id in self.consents and consent_type in self.consents[user_id]:
            self.consents[user_id][consent_type]['granted'] = False
            logger.info(f"Consent revoked: {user_id} - {consent_type}")
            return True
        return False

    def has_consent(self, user_id, consent_type):
        """Check if user has given consent"""
        if user_id in self.consents and consent_type in self.consents[user_id]:
            return self.consents[user_id][consent_type]['granted']
        return False


class AuditLogger:
    """Main audit logging system"""

    def __init__(self):
        self.events: List[AuditEvent] = []
        self.compliance_checks: Dict[str, ComplianceCheck] = {}
        self.compliance_reports: List[ComplianceReport] = []
        self.retention_policy = DataRetentionPolicy('default', 'Default retention policy')
        self.consent_manager = ConsentManager()
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default data retention policies"""
        self.retention_policy.set_retention_period('audit_logs', 365)  # 1 year
        self.retention_policy.set_retention_period('attendance_records', 730)  # 2 years
        self.retention_policy.set_retention_period('user_activity', 90)  # 90 days

    def log_event(self, event: AuditEvent):
        """Log audit event"""
        self.events.append(event)
        logger.info(f"Event logged: {event.event_type.value} - {event.resource}")
        return event.event_id

    def register_compliance_check(self, check: ComplianceCheck):
        """Register compliance check"""
        self.compliance_checks[check.check_id] = check
        logger.info(f"Compliance check registered: {check.check_name}")

    def execute_compliance_checks(self, standard: ComplianceStandard):
        """Execute compliance checks for standard"""
        report = ComplianceReport(self._generate_report_id(), standard)

        for check in self.compliance_checks.values():
            if check.standard == standard:
                check.execute()
                report.add_check_result(check)

        report.calculate_score()
        self.compliance_reports.append(report)
        logger.info(f"Compliance check completed for {standard.value}")
        return report

    def cleanup_expired_data(self):
        """Remove expired audit data"""
        expired_count = 0
        remaining_events = []

        for event in self.events:
            if not self.retention_policy.is_data_expired('audit_logs', event.timestamp):
                remaining_events.append(event)
            else:
                expired_count += 1

        self.events = remaining_events
        logger.info(f"Expired data cleanup: {expired_count} records removed")
        return expired_count

    def get_audit_trail(self, user_id=None, event_type=None, days=30):
        """Get audit trail"""
        cutoff_date = datetime.now() - timedelta(days=days)
        trail = []

        for event in self.events:
            if event.timestamp < cutoff_date:
                continue
            if user_id and event.user_id != user_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            trail.append(event.get_info())

        return trail

    def get_latest_compliance_report(self, standard: ComplianceStandard):
        """Get latest compliance report for standard"""
        for report in reversed(self.compliance_reports):
            if report.standard == standard:
                return report.get_report()
        return None

    def _generate_report_id(self):
        """Generate compliance report ID"""
        import uuid
        return str(uuid.uuid4())


# Global audit logger
global_audit_logger = AuditLogger()
