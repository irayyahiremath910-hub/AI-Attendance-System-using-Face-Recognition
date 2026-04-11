"""
Error Handling Utilities and Decorators for AI Attendance System
"""
import functools
import traceback
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from .exceptions import AttendanceSystemException
from .logging_config import get_app_logger, get_error_logger, get_face_logger


app_logger = get_app_logger()
error_logger = get_error_logger()
face_logger = get_face_logger()


def handle_exceptions(exception_type=AttendanceSystemException, log_level='ERROR', redirect_to='home'):
    """
    Decorator to handle exceptions in views
    
    Args:
        exception_type: Type of exception to catch
        log_level: Level of logging ('ERROR', 'WARNING', 'INFO')
        redirect_to: URL name or path to redirect on error
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except exception_type as e:
                error_msg = f"Exception in {view_func.__name__}: {str(e)}"
                
                # Log error with appropriate level
                if log_level == 'ERROR':
                    error_logger.error(error_msg, exc_info=True)
                elif log_level == 'WARNING':
                    app_logger.warning(error_msg)
                else:
                    app_logger.info(error_msg)
                
                # Add user-friendly message
                messages.error(request, f"An error occurred: {str(e)}")
                
                # Redirect to error page or home
                from django.shortcuts import redirect
                return redirect(redirect_to)
            except Exception as e:
                # Catch unexpected exceptions
                error_msg = f"Unexpected error in {view_func.__name__}: {str(e)}"
                error_logger.critical(error_msg, exc_info=True)
                messages.error(request, "An unexpected error occurred. Please contact administrator.")
                
                from django.shortcuts import redirect
                return redirect(redirect_to)
        return wrapper
    return decorator


def handle_face_recognition_errors(func):
    """
    Decorator specifically for face recognition operations
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            face_logger.info(f"Successfully executed: {func.__name__}")
            return result
        except ValueError as e:
            error_msg = f"Value error in {func.__name__}: {str(e)}"
            face_logger.error(error_msg)
            raise
        except RuntimeError as e:
            error_msg = f"Runtime error in {func.__name__}: {str(e)}"
            face_logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
            error_logger.critical(error_msg, exc_info=True)
            raise
    return wrapper


def handle_database_operations(func):
    """
    Decorator for database operations with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from .logging_config import get_database_logger
        db_logger = get_database_logger()
        
        try:
            result = func(*args, **kwargs)
            db_logger.info(f"Successfully executed: {func.__name__}")
            return result
        except Exception as e:
            error_msg = f"Database error in {func.__name__}: {str(e)}"
            db_logger.error(error_msg, exc_info=True)
            raise
    return wrapper


class ErrorResponse:
    """Helper class to generate error responses"""
    
    @staticmethod
    def json_error(message, status_code=400, error_type='error'):
        """Generate JSON error response"""
        return JsonResponse({
            'status': 'error',
            'message': message,
            'type': error_type
        }, status=status_code)
    
    @staticmethod
    def json_success(data=None, message='Success', status_code=200):
        """Generate JSON success response"""
        response = {
            'status': 'success',
            'message': message
        }
        if data:
            response['data'] = data
        return JsonResponse(response, status=status_code)


def log_function_call(logger=None, level='INFO'):
    """
    Decorator to log function calls with parameters and results
    
    Args:
        logger: Logger instance to use (defaults to app_logger)
        level: Log level ('INFO', 'DEBUG', 'WARNING', 'ERROR')
    """
    if logger is None:
        logger = app_logger
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log_msg_start = f"Calling {func.__name__} with args={args}, kwargs={kwargs}"
            
            if level == 'DEBUG':
                logger.debug(log_msg_start)
            else:
                logger.info(log_msg_start)
            
            try:
                result = func(*args, **kwargs)
                log_msg_end = f"Successfully completed {func.__name__}"
                
                if level == 'DEBUG':
                    logger.debug(f"{log_msg_end}. Result: {result}")
                else:
                    logger.info(log_msg_end)
                
                return result
            except Exception as e:
                error_msg = f"Error in {func.__name__}: {str(e)}"
                error_logger.error(error_msg, exc_info=True)
                raise
        return wrapper
    return decorator


def validate_input(validation_func):
    """
    Decorator to validate input before executing function
    
    Args:
        validation_func: Function that validates input and returns (is_valid, error_msg)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            is_valid, error_msg = validation_func(*args, **kwargs)
            
            if not is_valid:
                app_logger.warning(f"Validation failed in {func.__name__}: {error_msg}")
                raise ValueError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Context manager for exception handling
class ErrorContext:
    """Context manager for handling errors"""
    
    def __init__(self, logger_instance=None, operation_name='Operation'):
        self.logger = logger_instance or app_logger
        self.operation_name = operation_name
    
    def __enter__(self):
        self.logger.info(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation_name}")
            return False
        else:
            error_msg = f"Error in {self.operation_name}: {str(exc_val)}"
            error_logger.error(error_msg, exc_info=True)
            return False  # Re-raise the exception
