"""
Advanced logging and observability system
Structured logging, log aggregation, analysis, and insights
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log severity levels"""

    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class LogCategory(Enum):
    """Log categories"""

    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    DATA_ACCESS = 'data_access'
    BUSINESS_LOGIC = 'business_logic'
    PERFORMANCE = 'performance'
    SECURITY = 'security'
    SYSTEM = 'system'
    USER_ACTION = 'user_action'


class LogEntry:
    """Structured log entry"""

    def __init__(self, level: LogLevel, category: LogCategory, message, context=None):
        self.log_id = self._generate_id()
        self.timestamp = datetime.now()
        self.level = level
        self.category = category
        self.message = message
        self.context = context or {}
        self.source_file = None
        self.source_line = None
        self.user_id = None
        self.session_id = None
        self.duration_ms = 0
        self.metadata = {}

    def _generate_id(self):
        """Generate unique log ID"""
        import uuid
        return str(uuid.uuid4())

    def set_source(self, file_path, line_number):
        """Set source location"""
        self.source_file = file_path
        self.source_line = line_number

    def set_user_context(self, user_id, session_id):
        """Set user context"""
        self.user_id = user_id
        self.session_id = session_id

    def set_duration(self, duration_ms):
        """Set execution duration"""
        self.duration_ms = duration_ms

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'log_id': self.log_id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'category': self.category.value,
            'message': self.message,
            'context': self.context,
            'source_file': self.source_file,
            'source_line': self.source_line,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'duration_ms': self.duration_ms,
            'metadata': self.metadata,
        }

    def to_json(self):
        """Convert to JSON"""
        return json.dumps(self.to_dict(), default=str)


class LogBackend(ABC):
    """Base class for log backends"""

    def __init__(self, backend_name):
        self.backend_name = backend_name
        self.is_connected = False

    @abstractmethod
    def write(self, log_entry: LogEntry):
        """Write log entry"""
        pass

    @abstractmethod
    def read(self, filters=None, limit=100):
        """Read log entries"""
        pass

    @abstractmethod
    def close(self):
        """Close backend"""
        pass


class FileLogBackend(LogBackend):
    """File-based log storage"""

    def __init__(self, log_file_path):
        super().__init__('file')
        self.log_file_path = log_file_path
        self.entries = []
        self.is_connected = True

    def write(self, log_entry: LogEntry):
        """Write log to file"""
        try:
            self.entries.append(log_entry.to_dict())
            # In production, would write to actual file
            return True
        except Exception as e:
            logger.error(f"File log write failed: {str(e)}")
            return False

    def read(self, filters=None, limit=100):
        """Read logs from file"""
        results = self.entries
        
        if filters:
            if 'level' in filters:
                results = [r for r in results if r['level'] == filters['level']]
            if 'category' in filters:
                results = [r for r in results if r['category'] == filters['category']]
            if 'user_id' in filters:
                results = [r for r in results if r['user_id'] == filters['user_id']]

        return results[-limit:]

    def close(self):
        """Close backend"""
        self.is_connected = False


class DatabaseLogBackend(LogBackend):
    """Database-based log storage"""

    def __init__(self):
        super().__init__('database')
        self.logs = []
        self.is_connected = True

    def write(self, log_entry: LogEntry):
        """Write log to database"""
        try:
            self.logs.append(log_entry.to_dict())
            return True
        except Exception as e:
            logger.error(f"Database log write failed: {str(e)}")
            return False

    def read(self, filters=None, limit=100):
        """Read logs from database"""
        results = self.logs

        if filters:
            if 'level' in filters:
                results = [r for r in results if r['level'] == filters['level']]
            if 'category' in filters:
                results = [r for r in results if r['category'] == filters['category']]
            if 'user_id' in filters:
                results = [r for r in results if r['user_id'] == filters['user_id']]
            if 'date_from' in filters:
                results = [r for r in results if r['timestamp'] >= filters['date_from']]

        return results[-limit:]

    def close(self):
        """Close backend"""
        self.is_connected = False


class ElasticsearchLogBackend(LogBackend):
    """Elasticsearch log storage for advanced search"""

    def __init__(self, es_host='localhost:9200'):
        super().__init__('elasticsearch')
        self.es_host = es_host
        self.indices = {}
        self.is_connected = True

    def write(self, log_entry: LogEntry):
        """Write log to Elasticsearch"""
        try:
            index_name = f"logs-{log_entry.timestamp.strftime('%Y.%m.%d')}"
            if index_name not in self.indices:
                self.indices[index_name] = []
            self.indices[index_name].append(log_entry.to_dict())
            return True
        except Exception as e:
            logger.error(f"Elasticsearch write failed: {str(e)}")
            return False

    def read(self, filters=None, limit=100):
        """Search logs in Elasticsearch"""
        results = []
        for entries in self.indices.values():
            results.extend(entries)

        if filters:
            if 'level' in filters:
                results = [r for r in results if r['level'] == filters['level']]
            if 'search_query' in filters:
                query = filters['search_query'].lower()
                results = [r for r in results if query in r['message'].lower()]

        return results[-limit:]

    def close(self):
        """Close backend"""
        self.is_connected = False


class LogAnalyzer:
    """Analyze logs for insights"""

    def __init__(self, logs: List[Dict]):
        self.logs = logs

    def get_error_count(self):
        """Count errors"""
        return sum(1 for log in self.logs if log['level'] == 'error')

    def get_critical_count(self):
        """Count critical issues"""
        return sum(1 for log in self.logs if log['level'] == 'critical')

    def get_logs_by_level(self):
        """Get logs grouped by level"""
        by_level = {}
        for log in self.logs:
            level = log['level']
            by_level[level] = by_level.get(level, 0) + 1
        return by_level

    def get_logs_by_category(self):
        """Get logs grouped by category"""
        by_category = {}
        for log in self.logs:
            category = log['category']
            by_category[category] = by_category.get(category, 0) + 1
        return by_category

    def get_slow_operations(self, threshold_ms=1000):
        """Get slow operations"""
        return [log for log in self.logs if log['duration_ms'] > threshold_ms]

    def get_user_activity(self, user_id):
        """Get activity for user"""
        return [log for log in self.logs if log['user_id'] == user_id]

    def get_analytics(self):
        """Get analytics summary"""
        return {
            'total_logs': len(self.logs),
            'error_count': self.get_error_count(),
            'critical_count': self.get_critical_count(),
            'logs_by_level': self.get_logs_by_level(),
            'logs_by_category': self.get_logs_by_category(),
            'slow_operations_count': len(self.get_slow_operations()),
        }


class ObservabilityLogger:
    """Main observability logging system"""

    def __init__(self):
        self.backends: Dict[str, LogBackend] = {}
        self.current_logs = []
        self.log_retention_days = 90
        self._initialize_backends()

    def _initialize_backends(self):
        """Initialize default backends"""
        self.register_backend('file', FileLogBackend('/logs'))
        self.register_backend('database', DatabaseLogBackend())
        self.register_backend('elasticsearch', ElasticsearchLogBackend())

    def register_backend(self, backend_id, backend: LogBackend):
        """Register log backend"""
        self.backends[backend_id] = backend
        logger.info(f"Log backend registered: {backend_id}")

    def log(self, level: LogLevel, category: LogCategory, message, context=None, backend_ids=None):
        """Log event"""
        log_entry = LogEntry(level, category, message, context)
        self.current_logs.append(log_entry.to_dict())

        # Write to backends
        if backend_ids:
            for backend_id in backend_ids:
                if backend_id in self.backends:
                    self.backends[backend_id].write(log_entry)
        else:
            # Write to all backends
            for backend in self.backends.values():
                backend.write(log_entry)

        return log_entry.log_id

    def log_info(self, category: LogCategory, message, context=None):
        """Log info level"""
        return self.log(LogLevel.INFO, category, message, context)

    def log_warning(self, category: LogCategory, message, context=None):
        """Log warning level"""
        return self.log(LogLevel.WARNING, category, message, context)

    def log_error(self, category: LogCategory, message, context=None):
        """Log error level"""
        return self.log(LogLevel.ERROR, category, message, context)

    def log_critical(self, category: LogCategory, message, context=None):
        """Log critical level"""
        return self.log(LogLevel.CRITICAL, category, message, context)

    def search_logs(self, filters=None, backend_id='database', limit=100):
        """Search logs"""
        if backend_id in self.backends:
            backend = self.backends[backend_id]
            return backend.read(filters, limit)
        return []

    def get_analytics(self):
        """Get log analytics"""
        analyzer = LogAnalyzer(self.current_logs)
        return analyzer.get_analytics()

    def get_slow_queries(self, threshold_ms=1000):
        """Get slow operations"""
        analyzer = LogAnalyzer(self.current_logs)
        return analyzer.get_slow_operations(threshold_ms)

    def cleanup_old_logs(self, days=None):
        """Remove old logs"""
        cutoff_days = days or self.log_retention_days
        cutoff_date = datetime.now() - timedelta(days=cutoff_days)

        initial_count = len(self.current_logs)
        self.current_logs = [
            log for log in self.current_logs
            if datetime.fromisoformat(log['timestamp']) >= cutoff_date
        ]

        removed = initial_count - len(self.current_logs)
        logger.info(f"Cleaned up {removed} old logs")
        return removed

    def export_logs(self, format='json', filters=None):
        """Export logs"""
        logs = self.search_logs(filters)

        if format == 'json':
            return json.dumps(logs, indent=2, default=str)
        elif format == 'csv':
            import io
            import csv
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            return output.getvalue()

        return logs

    def get_health_check(self):
        """Check logging system health"""
        backend_status = {
            backend_id: backend.is_connected
            for backend_id, backend in self.backends.items()
        }

        analytics = self.get_analytics()

        return {
            'timestamp': datetime.now().isoformat(),
            'backend_status': backend_status,
            'recent_errors': analytics['error_count'],
            'recent_critical': analytics['critical_count'],
            'total_logs': analytics['total_logs'],
        }


# Global observability logger
global_observability_logger = ObservabilityLogger()
