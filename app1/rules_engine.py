"""
Intelligent attendance rules and policies engine
Defines and enforces attendance rules, policies, and business logic
"""

from datetime import date, time, timedelta, datetime
from app1.models import Student, Attendance
import logging

logger = logging.getLogger(__name__)


class AttendanceRule:
    """Base attendance rule class"""

    def __init__(self, rule_id, name, description):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.enabled = True

    def evaluate(self, student, attendance_record):
        """Evaluate rule for student and attendance"""
        raise NotImplementedError

    def execute_action(self, student, result):
        """Execute action when rule is triggered"""
        raise NotImplementedError


class LateArrivalRule(AttendanceRule):
    """Rule for late arrivals"""

    def __init__(self, threshold_minutes=15):
        super().__init__('late_arrival', 'Late Arrival Rule', 'Marks attendance as late if after threshold')
        self.threshold_minutes = threshold_minutes

    def evaluate(self, student, attendance_record):
        """Check if student is late"""
        if not attendance_record.check_in_time:
            return False

        from app1.config_utils import AppConfig
        start_time = datetime.strptime(AppConfig.CHECK_IN_START_TIME, '%H:%M').time()
        late_threshold = (datetime.combine(date.today(), start_time) + 
                         timedelta(minutes=self.threshold_minutes)).time()

        return attendance_record.check_in_time > late_threshold

    def execute_action(self, student, result):
        """Mark as late"""
        if result:
            logger.info(f"Late rule triggered for student {student.id}")
            return {'status': 'Late', 'reason': 'Arrived after threshold time'}
        return None


class AbsenteeRule(AttendanceRule):
    """Rule for detecting absentees"""

    def __init__(self, grace_period_hours=2):
        super().__init__('absentee', 'Absentee Rule', 'Marks as absent if not checked in')
        self.grace_period_hours = grace_period_hours

    def evaluate(self, student, attendance_record=None):
        """Check if student is absent"""
        if attendance_record:
            return attendance_record.status == 'Absent'

        # Check if no check-in by grace period
        from app1.config_utils import AppConfig
        deadline = datetime.strptime(AppConfig.CHECK_IN_END_TIME, '%H:%M').time()
        current_time = datetime.now().time()

        if current_time > deadline:
            today_records = Attendance.objects.filter(
                student=student,
                date=date.today()
            )
            return not today_records.exists()

        return False

    def execute_action(self, student, result):
        """Create absent record"""
        if result:
            logger.info(f"Absentee rule triggered for student {student.id}")
            return {'status': 'Absent', 'reason': 'No check-in'}
        return None


class ConsecutiveAbsentRule(AttendanceRule):
    """Rule for consecutive absences"""

    def __init__(self, consecutive_days=3):
        super().__init__('consecutive_absent', 'Consecutive Absences Rule', 
                        'Alert when student is absent for consecutive days')
        self.consecutive_days = consecutive_days

    def evaluate(self, student):
        """Check for consecutive absences"""
        absent_count = 0
        today = date.today()

        for i in range(self.consecutive_days):
            check_date = today - timedelta(days=i)
            record = Attendance.objects.filter(
                student=student,
                date=check_date
            ).first()

            if record and record.status == 'Absent':
                absent_count += 1
            else:
                absent_count = 0

            if absent_count >= self.consecutive_days:
                return True

        return False

    def execute_action(self, student, result):
        """Send alert for consecutive absences"""
        if result:
            logger.warning(f"Consecutive absence alert for student {student.id}")
            return {
                'alert_type': 'CONSECUTIVE_ABSENCE',
                'severity': 'HIGH',
                'message': f'Student absent for {self.consecutive_days} consecutive days'
            }
        return None


class AttendanceThresholdRule(AttendanceRule):
    """Rule for low attendance percentage"""

    def __init__(self, threshold_percent=75):
        super().__init__('attendance_threshold', 'Attendance Threshold Rule', 
                        'Alert when attendance percentage falls below threshold')
        self.threshold_percent = threshold_percent

    def evaluate(self, student, days=30):
        """Check if attendance percentage is below threshold"""
        start_date = date.today() - timedelta(days=days)
        records = Attendance.objects.filter(
            student=student,
            date__gte=start_date
        )

        if records.count() == 0:
            return False

        present_count = records.filter(status='Present').count()
        attendance_percent = (present_count / records.count()) * 100

        return attendance_percent < self.threshold_percent

    def execute_action(self, student, result):
        """Send low attendance alert"""
        if result:
            logger.warning(f"Low attendance alert for student {student.id}")
            return {
                'alert_type': 'LOW_ATTENDANCE',
                'severity': 'MEDIUM',
                'threshold': self.threshold_percent,
                'message': f'Attendance below {self.threshold_percent}%'
            }
        return None


class RuleEngine:
    """Engine for managing and evaluating attendance rules"""

    def __init__(self):
        self.rules = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default rules"""
        self.register_rule(LateArrivalRule())
        self.register_rule(AbsenteeRule())
        self.register_rule(ConsecutiveAbsentRule())
        self.register_rule(AttendanceThresholdRule())

    def register_rule(self, rule):
        """Register a rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Rule registered: {rule.name}")

    def unregister_rule(self, rule_id):
        """Unregister a rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Rule unregistered: {rule_id}")

    def enable_rule(self, rule_id):
        """Enable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True

    def disable_rule(self, rule_id):
        """Disable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False

    def evaluate_student(self, student):
        """Evaluate all rules for a student"""
        results = {
            'student_id': student.id,
            'evaluated_at': datetime.now().isoformat(),
            'alerts': [],
            'actions': [],
        }

        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue

            try:
                evaluation = rule.evaluate(student)
                if evaluation:
                    action = rule.execute_action(student, evaluation)
                    if action:
                        results['actions'].append(action)
                        results['alerts'].append({
                            'rule': rule.name,
                            'action': action,
                        })
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id}: {str(e)}")

        return results

    def evaluate_attendance(self, attendance_record):
        """Evaluate rules for attendance record"""
        results = {
            'attendance_id': attendance_record.id,
            'evaluated_at': datetime.now().isoformat(),
            'status': attendance_record.status,
            'actions': [],
        }

        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue

            try:
                if hasattr(rule, 'evaluate') and rule.__class__.__name__ in [
                    'LateArrivalRule', 'AbsenteeRule'
                ]:
                    evaluation = rule.evaluate(attendance_record.student, attendance_record)
                    if evaluation:
                        action = rule.execute_action(attendance_record.student, evaluation)
                        if action:
                            results['actions'].append(action)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id}: {str(e)}")

        return results

    def get_rule(self, rule_id):
        """Get rule by ID"""
        return self.rules.get(rule_id)

    def list_rules(self):
        """List all rules"""
        return [
            {
                'id': r.rule_id,
                'name': r.name,
                'description': r.description,
                'enabled': r.enabled,
            }
            for r in self.rules.values()
        ]


class PolicyEngine:
    """Engine for managing attendance policies"""

    POLICIES = {}

    @classmethod
    def define_policy(cls, policy_id, name, rules_config):
        """Define an attendance policy"""
        cls.POLICIES[policy_id] = {
            'id': policy_id,
            'name': name,
            'rules': rules_config,
            'created_at': datetime.now(),
        }
        logger.info(f"Policy defined: {name}")

    @classmethod
    def apply_policy(cls, policy_id, student):
        """Apply policy to a student"""
        if policy_id not in cls.POLICIES:
            return None

        policy = cls.POLICIES[policy_id]
        engine = RuleEngine()

        # Apply rules from policy
        for rule_config in policy['rules']:
            rule_id = rule_config.get('rule_id')
            if rule_id:
                rule = engine.get_rule(rule_id)
                if rule:
                    engine.evaluate_student(student)

        return policy

    @classmethod
    def list_policies(cls):
        """List all policies"""
        return list(cls.POLICIES.keys())


# Initialize global rule engine
global_rule_engine = RuleEngine()
