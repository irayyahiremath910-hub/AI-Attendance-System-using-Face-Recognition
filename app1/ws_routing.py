"""
Django Channels routing configuration for WebSockets
"""

from django.urls import re_path
from app1.websocket_consumers import (
    AttendanceLiveConsumer,
    AttendanceStatsConsumer,
    CameraControlConsumer
)

websocket_urlpatterns = [
    re_path(r'ws/attendance/live/$', AttendanceLiveConsumer.as_asgi()),
    re_path(r'ws/attendance/stats/$', AttendanceStatsConsumer.as_asgi()),
    re_path(r'ws/camera/control/$', CameraControlConsumer.as_asgi()),
]
