"""
Role-based access control and permission management system
Manages user roles, permissions, and access control policies
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import List, Set, Dict

logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions"""

    # Student permissions
    VIEW_STUDENT = 'view_student'
    CREATE_STUDENT = 'create_student'
    EDIT_STUDENT = 'edit_student'
    DELETE_STUDENT = 'delete_student'
    VIEW_OWN_ATTENDANCE = 'view_own_attendance'

    # Attendance permissions
    VIEW_ATTENDANCE = 'view_attendance'
    CREATE_ATTENDANCE = 'create_attendance'
    EDIT_ATTENDANCE = 'edit_attendance'
    DELETE_ATTENDANCE = 'delete_attendance'
    MARK_ATTENDANCE = 'mark_attendance'

    # Report permissions
    VIEW_REPORTS = 'view_reports'
    GENERATE_REPORTS = 'generate_reports'
    EXPORT_REPORTS = 'export_reports'

    # System permissions
    MANAGE_USERS = 'manage_users'
    MANAGE_ROLES = 'manage_roles'
    MANAGE_SETTINGS = 'manage_settings'
    VIEW_AUDIT_LOGS = 'view_audit_logs'
    MANAGE_NOTIFICATIONS = 'manage_notifications'

    # Admin permissions
    SYSTEM_ADMIN = 'system_admin'


class Role:
    """User role with associated permissions"""

    def __init__(self, role_id, role_name, description=''):
        self.role_id = role_id
        self.role_name = role_name
        self.description = description
        self.permissions: Set[Permission] = set()
        self.created_at = datetime.now()

    def add_permission(self, permission: Permission):
        """Add permission to role"""
        self.permissions.add(permission)
        logger.info(f"Permission added to {self.role_name}: {permission.value}")

    def remove_permission(self, permission: Permission):
        """Remove permission from role"""
        self.permissions.discard(permission)
        logger.info(f"Permission removed from {self.role_name}: {permission.value}")

    def has_permission(self, permission: Permission):
        """Check if role has permission"""
        return permission in self.permissions

    def get_permissions(self):
        """Get all permissions"""
        return [p.value for p in self.permissions]

    def get_info(self):
        """Get role information"""
        return {
            'role_id': self.role_id,
            'role_name': self.role_name,
            'description': self.description,
            'permissions': self.get_permissions(),
            'created_at': self.created_at.isoformat(),
        }


class User:
    """User with assigned roles"""

    def __init__(self, user_id, username, email):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.roles: List[Role] = []
        self.is_active = True
        self.created_at = datetime.now()
        self.last_login = None

    def assign_role(self, role: Role):
        """Assign role to user"""
        if role not in self.roles:
            self.roles.append(role)
            logger.info(f"Role assigned to {self.username}: {role.role_name}")

    def remove_role(self, role: Role):
        """Remove role from user"""
        if role in self.roles:
            self.roles.remove(role)
            logger.info(f"Role removed from {self.username}: {role.role_name}")

    def has_permission(self, permission: Permission):
        """Check if user has permission"""
        for role in self.roles:
            if role.has_permission(permission):
                return True
        return False

    def get_permissions(self):
        """Get all permissions from all roles"""
        permissions = set()
        for role in self.roles:
            permissions.update(role.permissions)
        return [p.value for p in permissions]

    def get_roles(self):
        """Get all roles"""
        return [role.role_name for role in self.roles]

    def update_last_login(self):
        """Update last login time"""
        self.last_login = datetime.now()

    def get_info(self):
        """Get user information"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'roles': self.get_roles(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class AccessPolicy:
    """Access control policy"""

    def __init__(self, policy_id, policy_name):
        self.policy_id = policy_id
        self.policy_name = policy_name
        self.rules = []
        self.created_at = datetime.now()

    def add_rule(self, rule_condition, action='allow'):
        """Add policy rule"""
        self.rules.append({
            'condition': rule_condition,
            'action': action,
        })
        logger.info(f"Rule added to policy {self.policy_name}")

    def evaluate(self, context):
        """Evaluate policy against context"""
        for rule in self.rules:
            # Evaluate rule condition
            if rule['condition'](context):
                return rule['action'] == 'allow'
        return False

    def get_info(self):
        """Get policy information"""
        return {
            'policy_id': self.policy_id,
            'policy_name': self.policy_name,
            'rule_count': len(self.rules),
            'created_at': self.created_at.isoformat(),
        }


class AccessControlManager:
    """Main access control manager"""

    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.policies: Dict[str, AccessPolicy] = {}
        self.access_log = []
        self._initialize_default_roles()

    def _initialize_default_roles(self):
        """Initialize default system roles"""
        # Admin role
        admin_role = Role('admin', 'Administrator', 'Full system access')
        for perm in Permission:
            admin_role.add_permission(perm)
        self.roles['admin'] = admin_role

        # Teacher role
        teacher_role = Role('teacher', 'Teacher', 'Can manage attendance and view reports')
        teacher_role.add_permission(Permission.VIEW_STUDENT)
        teacher_role.add_permission(Permission.CREATE_ATTENDANCE)
        teacher_role.add_permission(Permission.EDIT_ATTENDANCE)
        teacher_role.add_permission(Permission.VIEW_ATTENDANCE)
        teacher_role.add_permission(Permission.MARK_ATTENDANCE)
        teacher_role.add_permission(Permission.VIEW_REPORTS)
        teacher_role.add_permission(Permission.GENERATE_REPORTS)
        self.roles['teacher'] = teacher_role

        # Student role
        student_role = Role('student', 'Student', 'Can view own attendance')
        student_role.add_permission(Permission.VIEW_OWN_ATTENDANCE)
        self.roles['student'] = student_role

        # Guest role
        guest_role = Role('guest', 'Guest', 'Read-only access')
        guest_role.add_permission(Permission.VIEW_STUDENT)
        self.roles['guest'] = guest_role

        logger.info("Default roles initialized")

    def create_role(self, role_id, role_name, description=''):
        """Create new role"""
        role = Role(role_id, role_name, description)
        self.roles[role_id] = role
        logger.info(f"Role created: {role_name}")
        return role

    def get_role(self, role_id):
        """Get role by ID"""
        return self.roles.get(role_id)

    def create_user(self, user_id, username, email):
        """Create new user"""
        user = User(user_id, username, email)
        self.users[user_id] = user
        logger.info(f"User created: {username}")
        return user

    def get_user(self, user_id):
        """Get user by ID"""
        return self.users.get(user_id)

    def assign_role_to_user(self, user_id, role_id):
        """Assign role to user"""
        user = self.get_user(user_id)
        role = self.get_role(role_id)

        if user and role:
            user.assign_role(role)
            return True
        return False

    def check_permission(self, user_id, permission: Permission):
        """Check if user has permission"""
        user = self.get_user(user_id)
        if user:
            result = user.has_permission(permission)
            self._log_access(user_id, permission.value, result)
            return result
        return False

    def create_policy(self, policy_id, policy_name):
        """Create access policy"""
        policy = AccessPolicy(policy_id, policy_name)
        self.policies[policy_id] = policy
        logger.info(f"Policy created: {policy_name}")
        return policy

    def evaluate_policy(self, policy_id, context):
        """Evaluate access policy"""
        policy = self.policies.get(policy_id)
        if policy:
            return policy.evaluate(context)
        return False

    def _log_access(self, user_id, resource, granted):
        """Log access attempt"""
        self.access_log.append({
            'user_id': user_id,
            'resource': resource,
            'granted': granted,
            'timestamp': datetime.now(),
        })

    def get_access_log(self, user_id=None, limit=100):
        """Get access log"""
        log = self.access_log
        if user_id:
            log = [entry for entry in log if entry['user_id'] == user_id]
        return log[-limit:]

    def get_user_permissions(self, user_id):
        """Get all permissions for user"""
        user = self.get_user(user_id)
        if user:
            return user.get_permissions()
        return []

    def revoke_user_access(self, user_id):
        """Revoke all access for user"""
        user = self.get_user(user_id)
        if user:
            user.is_active = False
            logger.warning(f"Access revoked for user: {user.username}")
            return True
        return False

    def grant_user_access(self, user_id):
        """Grant access for user"""
        user = self.get_user(user_id)
        if user:
            user.is_active = True
            logger.info(f"Access granted for user: {user.username}")
            return True
        return False


# Global access control manager
global_access_manager = AccessControlManager()
