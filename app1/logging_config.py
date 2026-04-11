"""
Logging Configuration for AI Attendance System
"""
import logging
import logging.handlers
import os
from django.conf import settings

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Define log file paths
APP_LOG_FILE = os.path.join(LOGS_DIR, 'app.log')
ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'errors.log')
FACE_RECOGNITION_LOG_FILE = os.path.join(LOGS_DIR, 'face_recognition.log')
DATABASE_LOG_FILE = os.path.join(LOGS_DIR, 'database.log')

# Configure root logger
ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.setLevel(logging.DEBUG)

# Create formatters
standard_formatter = logging.Formatter(
    '[%(asctime)s] %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

detailed_formatter = logging.Formatter(
    '[%(asctime)s] %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s() - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# App Logger (General application logs)
app_logger = logging.getLogger('attendance.app')
app_logger.setLevel(logging.INFO)
app_handler = logging.handlers.RotatingFileHandler(
    APP_LOG_FILE, maxBytes=10485760, backupCount=5  # 10MB per file, keep 5 backups
)
app_handler.setFormatter(standard_formatter)
app_logger.addHandler(app_handler)

# Console handler for app logger (DEBUG in development)
if settings.DEBUG:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(standard_formatter)
    app_logger.addHandler(console_handler)

# Error Logger (Only errors and critical issues)
error_logger = logging.getLogger('attendance.errors')
error_logger.setLevel(logging.ERROR)
error_handler = logging.handlers.RotatingFileHandler(
    ERROR_LOG_FILE, maxBytes=10485760, backupCount=10
)
error_handler.setFormatter(detailed_formatter)
error_logger.addHandler(error_handler)

# Face Recognition Logger (Face detection and recognition specific)
face_logger = logging.getLogger('attendance.face_recognition')
face_logger.setLevel(logging.INFO)
face_handler = logging.handlers.RotatingFileHandler(
    FACE_RECOGNITION_LOG_FILE, maxBytes=5242880, backupCount=5  # 5MB per file
)
face_handler.setFormatter(standard_formatter)
face_logger.addHandler(face_handler)

# Database Logger (Database operations)
database_logger = logging.getLogger('attendance.database')
database_logger.setLevel(logging.INFO)
db_handler = logging.handlers.RotatingFileHandler(
    DATABASE_LOG_FILE, maxBytes=5242880, backupCount=5
)
db_handler.setFormatter(standard_formatter)
database_logger.addHandler(db_handler)

# Prevent duplicate handlers
app_logger.propagate = False
error_logger.propagate = False
face_logger.propagate = False
database_logger.propagate = False


def get_app_logger():
    """Get the general application logger"""
    return app_logger


def get_error_logger():
    """Get the error logger"""
    return error_logger


def get_face_logger():
    """Get the face recognition logger"""
    return face_logger


def get_database_logger():
    """Get the database logger"""
    return database_logger
