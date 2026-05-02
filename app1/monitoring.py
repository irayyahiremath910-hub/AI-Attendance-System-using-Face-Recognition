"""
System monitoring and health check system
Monitors application health, performance, and dependencies
"""

from datetime import datetime, timedelta
import logging
import psutil
import json

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants"""

    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'
    UNKNOWN = 'unknown'


class ServiceHealthCheck:
    """Base health check for services"""

    def __init__(self, service_name):
        self.service_name = service_name
        self.last_check = None
        self.status = HealthStatus.UNKNOWN

    def check(self):
        """Check service health"""
        raise NotImplementedError

    def get_status(self):
        """Get current status"""
        return {
            'service': self.service_name,
            'status': self.status,
            'last_check': self.last_check.isoformat() if self.last_check else None,
        }


class DatabaseHealthCheck(ServiceHealthCheck):
    """Check database health"""

    def __init__(self):
        super().__init__('database')

    def check(self):
        """Check database connectivity"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            self.status = HealthStatus.HEALTHY
            self.last_check = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            self.status = HealthStatus.UNHEALTHY
            self.last_check = datetime.now()
            return False


class CacheHealthCheck(ServiceHealthCheck):
    """Check cache service health"""

    def __init__(self):
        super().__init__('cache')

    def check(self):
        """Check cache connectivity"""
        try:
            from django.core.cache import cache
            test_key = 'health_check_test'
            cache.set(test_key, 'ok', 10)
            result = cache.get(test_key)
            
            if result == 'ok':
                self.status = HealthStatus.HEALTHY
            else:
                self.status = HealthStatus.DEGRADED
            
            self.last_check = datetime.now()
            return self.status == HealthStatus.HEALTHY
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            self.status = HealthStatus.UNHEALTHY
            self.last_check = datetime.now()
            return False


class EmailHealthCheck(ServiceHealthCheck):
    """Check email service health"""

    def __init__(self):
        super().__init__('email')

    def check(self):
        """Check email service"""
        try:
            from django.core.mail import get_connection
            connection = get_connection()
            connection.open()
            connection.close()
            
            self.status = HealthStatus.HEALTHY
            self.last_check = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Email health check failed: {str(e)}")
            self.status = HealthStatus.DEGRADED
            self.last_check = datetime.now()
            return False


class SystemResourceMonitor:
    """Monitor system resources"""

    @staticmethod
    def get_cpu_usage():
        """Get CPU usage percentage"""
        return psutil.cpu_percent(interval=1)

    @staticmethod
    def get_memory_usage():
        """Get memory usage percentage"""
        return psutil.virtual_memory().percent

    @staticmethod
    def get_disk_usage():
        """Get disk usage percentage"""
        return psutil.disk_usage('/').percent

    @staticmethod
    def get_system_metrics():
        """Get all system metrics"""
        return {
            'cpu_percent': SystemResourceMonitor.get_cpu_usage(),
            'memory_percent': SystemResourceMonitor.get_memory_usage(),
            'disk_percent': SystemResourceMonitor.get_disk_usage(),
            'timestamp': datetime.now().isoformat(),
        }

    @staticmethod
    def is_resource_healthy():
        """Check if resources are within acceptable limits"""
        metrics = SystemResourceMonitor.get_system_metrics()
        
        thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
        }

        for metric, threshold in thresholds.items():
            if metrics[metric] > threshold:
                return False

        return True


class ApplicationMetrics:
    """Track application performance metrics"""

    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'average_response_time': 0,
            'uptime_seconds': 0,
            'start_time': datetime.now(),
        }

    def record_request(self, success=True, response_time=0):
        """Record API request"""
        self.metrics['requests_total'] += 1
        if success:
            self.metrics['requests_success'] += 1
        else:
            self.metrics['requests_error'] += 1

    def get_uptime(self):
        """Get application uptime"""
        uptime = datetime.now() - self.metrics['start_time']
        return uptime.total_seconds()

    def get_metrics(self):
        """Get all metrics"""
        error_rate = (
            self.metrics['requests_error'] / self.metrics['requests_total'] * 100
            if self.metrics['requests_total'] > 0 else 0
        )

        return {
            'requests_total': self.metrics['requests_total'],
            'requests_success': self.metrics['requests_success'],
            'requests_error': self.metrics['requests_error'],
            'error_rate_percent': round(error_rate, 2),
            'uptime_seconds': int(self.get_uptime()),
            'start_time': self.metrics['start_time'].isoformat(),
        }

    def reset(self):
        """Reset metrics"""
        self.metrics['requests_total'] = 0
        self.metrics['requests_success'] = 0
        self.metrics['requests_error'] = 0
        self.metrics['start_time'] = datetime.now()


class HealthCheckAggregator:
    """Aggregate health checks from multiple services"""

    def __init__(self):
        self.checks = []
        self._register_default_checks()

    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check(DatabaseHealthCheck())
        self.register_check(CacheHealthCheck())
        self.register_check(EmailHealthCheck())

    def register_check(self, health_check):
        """Register health check"""
        self.checks.append(health_check)
        logger.info(f"Health check registered: {health_check.service_name}")

    def run_all_checks(self):
        """Run all health checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'overall_status': HealthStatus.HEALTHY,
        }

        for check in self.checks:
            check.check()
            results['checks'].append(check.get_status())

            if check.status == HealthStatus.UNHEALTHY:
                results['overall_status'] = HealthStatus.UNHEALTHY
            elif check.status == HealthStatus.DEGRADED and results['overall_status'] != HealthStatus.UNHEALTHY:
                results['overall_status'] = HealthStatus.DEGRADED

        return results

    def get_health_report(self):
        """Get comprehensive health report"""
        health = self.run_all_checks()
        system_metrics = SystemResourceMonitor.get_system_metrics()
        resource_healthy = SystemResourceMonitor.is_resource_healthy()

        return {
            'application_health': health,
            'system_resources': system_metrics,
            'resource_status': 'healthy' if resource_healthy else 'warning',
            'generated_at': datetime.now().isoformat(),
        }


class PerformanceMonitor:
    """Monitor application performance"""

    def __init__(self):
        self.slowest_endpoints = []
        self.most_common_errors = {}

    def record_endpoint_time(self, endpoint, response_time):
        """Record endpoint response time"""
        self.slowest_endpoints.append({
            'endpoint': endpoint,
            'response_time': response_time,
            'timestamp': datetime.now(),
        })

        # Keep only last 100
        if len(self.slowest_endpoints) > 100:
            self.slowest_endpoints = self.slowest_endpoints[-100:]

    def record_error(self, error_type):
        """Record error occurrence"""
        if error_type not in self.most_common_errors:
            self.most_common_errors[error_type] = 0
        self.most_common_errors[error_type] += 1

    def get_slowest_endpoints(self, limit=10):
        """Get slowest endpoints"""
        sorted_endpoints = sorted(
            self.slowest_endpoints,
            key=lambda x: x['response_time'],
            reverse=True
        )
        return sorted_endpoints[:limit]

    def get_error_summary(self):
        """Get error summary"""
        return self.most_common_errors

    def get_performance_report(self):
        """Get performance report"""
        return {
            'slowest_endpoints': self.get_slowest_endpoints(),
            'error_summary': self.get_error_summary(),
            'generated_at': datetime.now().isoformat(),
        }


# Global instances
global_aggregator = HealthCheckAggregator()
global_metrics = ApplicationMetrics()
global_performance = PerformanceMonitor()
