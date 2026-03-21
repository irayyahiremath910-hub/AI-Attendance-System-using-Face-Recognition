import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project101.settings')

app = Celery('Project101')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    'send-low-attendance-alerts': {
        'task': 'app1.tasks.send_low_attendance_alerts',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'check-absent-students': {
        'task': 'app1.tasks.check_absent_students',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8 AM
    },
    'update-attendance-summary': {
        'task': 'app1.tasks.update_attendance_summary',
        'schedule': crontab(hour='*/12'),  # Every 12 hours
    },
    'send-weekly-report': {
        'task': 'app1.tasks.send_weekly_report',
        'schedule': crontab(day_of_week=0, hour=9, minute=0),  # Every Monday at 9 AM
    },
}


@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def debug_task(self):
    print(f'Request: {self.request!r}')
