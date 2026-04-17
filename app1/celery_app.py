"""
Celery task queue configuration for background jobs
Handles scheduled tasks like notifications, exports, and batch operations
"""

from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project101.settings')

app = Celery('attendance_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'app1.celery_tasks.send_daily_attendance_reminders',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    'send-weekly-reports': {
        'task': 'app1.celery_tasks.send_weekly_reports',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM
    },
    'check-system-health': {
        'task': 'app1.celery_tasks.check_system_health',
        'schedule': crontab(minute=0),  # Every hour
    },
    'generate-daily-analytics': {
        'task': 'app1.celery_tasks.generate_daily_analytics',
        'schedule': crontab(hour=23, minute=59),  # 11:59 PM daily
    },
    'cleanup-old-records': {
        'task': 'app1.celery_tasks.cleanup_old_attendance_records',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task"""
    print(f'Request: {self.request!r}')
