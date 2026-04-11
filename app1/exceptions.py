"""
Custom Exception Classes for AI Attendance System
"""


class AttendanceSystemException(Exception):
    """Base exception for all attendance system errors"""
    pass


class FaceRecognitionException(AttendanceSystemException):
    """Raised when face recognition fails"""
    pass


class FaceDetectionException(FaceRecognitionException):
    """Raised when face detection fails"""
    pass


class FaceEncodingException(FaceRecognitionException):
    """Raised when face encoding fails"""
    pass


class InvalidStudentException(AttendanceSystemException):
    """Raised when student data is invalid"""
    pass


class CameraException(AttendanceSystemException):
    """Raised when camera operations fail"""
    pass


class DatabaseException(AttendanceSystemException):
    """Raised when database operations fail"""
    pass


class AttendanceRecordException(DatabaseException):
    """Raised when attendance recording fails"""
    pass


class ImageProcessingException(AttendanceSystemException):
    """Raised when image processing fails"""
    pass


class AuthenticationException(AttendanceSystemException):
    """Raised when authentication fails"""
    pass
