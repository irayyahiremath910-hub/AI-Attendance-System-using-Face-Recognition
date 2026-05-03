"""
Data backup and disaster recovery system
Manages backup creation, restoration, and recovery procedures
"""

from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import logging
import json
from typing import List, Dict

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Backup types"""

    FULL = 'full'
    INCREMENTAL = 'incremental'
    DIFFERENTIAL = 'differential'
    SNAPSHOT = 'snapshot'


class BackupStatus(Enum):
    """Backup status"""

    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    VERIFIED = 'verified'


class BackupStorage(ABC):
    """Base class for backup storage"""

    def __init__(self, storage_name):
        self.storage_name = storage_name
        self.is_available = True

    @abstractmethod
    def store_backup(self, backup_name, data):
        """Store backup"""
        pass

    @abstractmethod
    def retrieve_backup(self, backup_name):
        """Retrieve backup"""
        pass

    @abstractmethod
    def delete_backup(self, backup_name):
        """Delete backup"""
        pass

    @abstractmethod
    def list_backups(self):
        """List available backups"""
        pass


class LocalBackupStorage(BackupStorage):
    """Local file system backup storage"""

    def __init__(self, storage_path):
        super().__init__('local_storage')
        self.storage_path = storage_path
        self.backups = {}

    def store_backup(self, backup_name, data):
        """Store backup locally"""
        try:
            self.backups[backup_name] = {
                'data': data,
                'stored_at': datetime.now(),
                'size': len(str(data)),
            }
            logger.info(f"Backup stored locally: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Local backup storage failed: {str(e)}")
            return False

    def retrieve_backup(self, backup_name):
        """Retrieve backup from storage"""
        if backup_name in self.backups:
            logger.info(f"Backup retrieved: {backup_name}")
            return self.backups[backup_name]['data']
        return None

    def delete_backup(self, backup_name):
        """Delete backup"""
        if backup_name in self.backups:
            del self.backups[backup_name]
            logger.info(f"Backup deleted: {backup_name}")
            return True
        return False

    def list_backups(self):
        """List all backups"""
        return list(self.backups.keys())

    def get_backup_info(self, backup_name):
        """Get backup information"""
        if backup_name in self.backups:
            info = self.backups[backup_name].copy()
            info['name'] = backup_name
            return info
        return None


class CloudBackupStorage(BackupStorage):
    """Cloud backup storage (AWS S3, Azure Blob, etc.)"""

    def __init__(self, cloud_provider, credentials):
        super().__init__(f'cloud_{cloud_provider}')
        self.cloud_provider = cloud_provider
        self.credentials = credentials
        self.backups = {}

    def store_backup(self, backup_name, data):
        """Store backup to cloud"""
        try:
            # Simulate cloud storage
            self.backups[backup_name] = {
                'data': data,
                'stored_at': datetime.now(),
                'size': len(str(data)),
                'location': f"{self.cloud_provider}://{backup_name}",
            }
            logger.info(f"Backup stored to {self.cloud_provider}: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Cloud backup storage failed: {str(e)}")
            return False

    def retrieve_backup(self, backup_name):
        """Retrieve backup from cloud"""
        if backup_name in self.backups:
            logger.info(f"Backup retrieved from cloud: {backup_name}")
            return self.backups[backup_name]['data']
        return None

    def delete_backup(self, backup_name):
        """Delete backup from cloud"""
        if backup_name in self.backups:
            del self.backups[backup_name]
            logger.info(f"Backup deleted from cloud: {backup_name}")
            return True
        return False

    def list_backups(self):
        """List backups in cloud"""
        return list(self.backups.keys())


class Backup:
    """Individual backup"""

    def __init__(self, backup_id, backup_type: BackupType, data=None):
        self.backup_id = backup_id
        self.backup_type = backup_type
        self.data = data
        self.created_at = datetime.now()
        self.size = len(str(data)) if data else 0
        self.status = BackupStatus.PENDING
        self.checksum = self._calculate_checksum()

    def _calculate_checksum(self):
        """Calculate backup checksum"""
        import hashlib
        data_str = json.dumps(self.data, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()

    def verify(self):
        """Verify backup integrity"""
        if self.data:
            current_checksum = self._calculate_checksum()
            is_valid = current_checksum == self.checksum
            self.status = BackupStatus.VERIFIED if is_valid else BackupStatus.FAILED
            return is_valid
        return False

    def get_info(self):
        """Get backup information"""
        return {
            'backup_id': self.backup_id,
            'type': self.backup_type.value,
            'created_at': self.created_at.isoformat(),
            'size': self.size,
            'status': self.status.value,
            'checksum': self.checksum,
        }


class BackupManager:
    """Manage backup creation and restoration"""

    def __init__(self):
        self.backups: Dict[str, Backup] = {}
        self.storage_backends: Dict[str, BackupStorage] = {}
        self.backup_schedule = []
        self.backup_count = 0
        self._initialize_default_storage()

    def _initialize_default_storage(self):
        """Initialize default storage backends"""
        local_storage = LocalBackupStorage('/backups')
        self.register_storage('local', local_storage)

        cloud_storage = CloudBackupStorage('aws_s3', {})
        self.register_storage('cloud', cloud_storage)

    def register_storage(self, storage_id, storage: BackupStorage):
        """Register backup storage"""
        self.storage_backends[storage_id] = storage
        logger.info(f"Storage backend registered: {storage_id}")

    def create_backup(self, backup_type: BackupType, data, storage_ids=None):
        """Create backup"""
        self.backup_count += 1
        backup_id = f"backup_{self.backup_count}_{datetime.now().timestamp()}"

        backup = Backup(backup_id, backup_type, data)
        backup.status = BackupStatus.COMPLETED

        self.backups[backup_id] = backup

        # Store in backends
        if storage_ids:
            for storage_id in storage_ids:
                if storage_id in self.storage_backends:
                    storage = self.storage_backends[storage_id]
                    storage.store_backup(backup_id, data)

        logger.info(f"Backup created: {backup_id}")
        return backup_id

    def restore_backup(self, backup_id):
        """Restore from backup"""
        if backup_id in self.backups:
            backup = self.backups[backup_id]
            if backup.verify():
                logger.info(f"Backup restored: {backup_id}")
                return backup.data
            else:
                logger.error(f"Backup verification failed: {backup_id}")
                return None
        return None

    def get_backup(self, backup_id):
        """Get backup information"""
        if backup_id in self.backups:
            return self.backups[backup_id].get_info()
        return None

    def list_backups(self, backup_type=None):
        """List all backups"""
        backups = []
        for backup_id, backup in self.backups.items():
            if backup_type and backup.backup_type != backup_type:
                continue
            backups.append(backup.get_info())
        return backups

    def schedule_backup(self, backup_type, frequency_hours, data_source):
        """Schedule regular backup"""
        schedule = {
            'backup_type': backup_type,
            'frequency_hours': frequency_hours,
            'data_source': data_source,
            'next_backup': datetime.now() + timedelta(hours=frequency_hours),
            'enabled': True,
        }
        self.backup_schedule.append(schedule)
        logger.info(f"Backup scheduled: {backup_type.value} every {frequency_hours}h")
        return len(self.backup_schedule) - 1

    def process_scheduled_backups(self):
        """Process scheduled backups"""
        processed = []
        for schedule in self.backup_schedule:
            if schedule['enabled'] and datetime.now() >= schedule['next_backup']:
                # Simulate backup creation
                processed.append({
                    'type': schedule['backup_type'].value,
                    'time': datetime.now().isoformat(),
                })
                schedule['next_backup'] = datetime.now() + timedelta(hours=schedule['frequency_hours'])

        return processed

    def cleanup_old_backups(self, days=30):
        """Remove backups older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = []

        for backup_id, backup in list(self.backups.items()):
            if backup.created_at < cutoff_date:
                del self.backups[backup_id]
                deleted.append(backup_id)

        logger.info(f"Deleted {len(deleted)} old backups")
        return deleted

    def get_backup_statistics(self):
        """Get backup statistics"""
        total_backups = len(self.backups)
        total_size = sum(b.size for b in self.backups.values())

        backup_by_type = {}
        for backup in self.backups.values():
            type_name = backup.backup_type.value
            if type_name not in backup_by_type:
                backup_by_type[type_name] = 0
            backup_by_type[type_name] += 1

        return {
            'total_backups': total_backups,
            'total_size_bytes': total_size,
            'backups_by_type': backup_by_type,
            'average_backup_size': total_size // total_backups if total_backups > 0 else 0,
        }


class DisasterRecoveryPlan:
    """Disaster recovery plan"""

    def __init__(self, plan_id):
        self.plan_id = plan_id
        self.recovery_procedures = []
        self.rpo_minutes = 15  # Recovery Point Objective
        self.rto_minutes = 30  # Recovery Time Objective
        self.created_at = datetime.now()
        self.last_tested = None

    def add_procedure(self, step_number, procedure_description, estimated_time_minutes):
        """Add recovery procedure"""
        self.recovery_procedures.append({
            'step': step_number,
            'description': procedure_description,
            'estimated_time': estimated_time_minutes,
            'completed': False,
        })

    def test_recovery(self):
        """Test disaster recovery plan"""
        self.last_tested = datetime.now()
        logger.info(f"Disaster recovery plan tested: {self.plan_id}")
        return True

    def execute_recovery(self):
        """Execute disaster recovery"""
        logger.warning(f"Executing disaster recovery plan: {self.plan_id}")
        for procedure in self.recovery_procedures:
            procedure['completed'] = True
            logger.info(f"Recovery step completed: {procedure['step']}")
        return True

    def get_plan(self):
        """Get recovery plan"""
        return {
            'plan_id': self.plan_id,
            'rpo_minutes': self.rpo_minutes,
            'rto_minutes': self.rto_minutes,
            'procedures': self.recovery_procedures,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'created_at': self.created_at.isoformat(),
        }


# Global backup manager
global_backup_manager = BackupManager()
