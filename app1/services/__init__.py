# Services module for AI Attendance System
from .face_recognition import FaceRecognitionService
from .attendance import AttendanceService

__all__ = ['FaceRecognitionService', 'AttendanceService']
