"""Swagger/OpenAPI Documentation Configuration - Day 8

This module configures Swagger UI and OpenAPI schema generation for the REST API.
Provides comprehensive API documentation with examples and use cases.
"""

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class EnhancedSchema(AutoSchema):
    """Enhanced schema generation with better descriptions."""
    
    target_class = AutoSchema
    
    def get_operation_id(self, path, method):
        """Generate meaningful operation IDs."""
        operation_id = super().get_operation_id(path, method)
        return operation_id or f"{method}_{path.replace('/', '_')}"
    
    def get_request_body(self, path, method):
        """Add request body description."""
        request_body = super().get_request_body(path, method)
        if request_body and method in ['POST', 'PUT', 'PATCH']:
            request_body['description'] = f"{method} operation for API resource"
        return request_body


# API Documentation Schemas
API_DOCUMENTATION = {
    "title": "AI Attendance System - REST API",
    "description": """
        Comprehensive REST API for AI-powered attendance management system.
        
        Features:
        - Face recognition enrollment and verification
        - Real-time attendance tracking
        - Advanced filtering and search
        - Pagination with multiple strategies
        - Bulk operations
        - Analytics and reporting
        - Admin dashboard
        
        Authentication: Token-based authentication required
        Rate Limiting: 1000 requests per hour
    """,
    "version": "1.0.0",
    "contact": {
        "name": "Support",
        "email": "support@aiattendance.com"
    },
    "license": {
        "name": "MIT"
    }
}

# Endpoint Documentation
ENDPOINTS_DOCUMENTATION = {
    "students": {
        "list": {
            "summary": "List all students",
            "description": "Retrieve a paginated list of students with advanced filtering options",
            "parameters": [
                {
                    "name": "name",
                    "description": "Filter by student name (case-insensitive partial match)",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"}
                },
                {
                    "name": "email",
                    "description": "Filter by student email",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"}
                },
                {
                    "name": "authorized",
                    "description": "Filter by authorization status (true/false)",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "boolean"}
                },
                {
                    "name": "student_class",
                    "description": "Filter by class",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"}
                },
                {
                    "name": "search",
                    "description": "Multi-field search across name, email, and class",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"}
                },
                {
                    "name": "ordering",
                    "description": "Order results by field. Prefix with '-' for descending.",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"}
                },
                {
                    "name": "page",
                    "description": "Page number for pagination",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer"}
                },
                {
                    "name": "page_size",
                    "description": "Items per page (default: 20, max: 100)",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer"}
                }
            ],
            "example_response": {
                "total_count": 150,
                "total_pages": 8,
                "current_page": 1,
                "page_size": 20,
                "next": "http://api.example.com/api/students/?page=2",
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "phone_number": "+1-234-567-8900",
                        "student_class": "A",
                        "authorized": True,
                        "created_at": "2026-04-20T10:00:00Z"
                    }
                ]
            }
        },
        "create": {
            "summary": "Create a new student",
            "description": "Add a new student to the system",
            "request_body": {
                "name": "string (2-100 chars)",
                "email": "string (valid email)",
                "phone_number": "string (optional)",
                "student_class": "string",
                "authorized": "boolean"
            }
        },
        "retrieve": {
            "summary": "Get student details",
            "description": "Retrieve full details of a specific student with attendance information",
            "response": {
                "id": "integer",
                "name": "string",
                "email": "string",
                "total_attendance": "integer",
                "latest_attendance": "object or null",
                "recent_attendance": "array"
            }
        },
        "bulk_authorize": {
            "summary": "Authorize multiple students",
            "description": "Bulk authorize students for face recognition",
            "request_body": {
                "student_ids": "array of integers (1-100 items)"
            },
            "response": {
                "success": "boolean",
                "authorized_count": "integer",
                "total_authorized": "integer",
                "total_students": "integer",
                "authorization_rate": "float"
            }
        },
        "attendance_history": {
            "summary": "Get student attendance history",
            "description": "Retrieve paginated attendance records for a student",
            "parameters": [
                {
                    "name": "days",
                    "description": "Number of days to retrieve (default: 30)",
                    "schema": {"type": "integer"}
                },
                {
                    "name": "page",
                    "description": "Page number",
                    "schema": {"type": "integer"}
                }
            ]
        }
    },
    "attendance": {
        "list": {
            "summary": "List attendance records",
            "description": "Retrieve paginated attendance records with advanced filtering",
            "parameters": [
                {
                    "name": "student_name",
                    "description": "Filter by student name",
                    "schema": {"type": "string"}
                },
                {
                    "name": "date_from",
                    "description": "Start date (YYYY-MM-DD format)",
                    "schema": {"type": "string"}
                },
                {
                    "name": "date_to",
                    "description": "End date (YYYY-MM-DD format)",
                    "schema": {"type": "string"}
                },
                {
                    "name": "has_check_in",
                    "description": "Filter by check-in presence",
                    "schema": {"type": "boolean"}
                },
                {
                    "name": "has_check_out",
                    "description": "Filter by check-out presence",
                    "schema": {"type": "boolean"}
                }
            ]
        },
        "check_in": {
            "summary": "Mark attendance check-in",
            "description": "Check in a student for attendance",
            "response": {
                "status": "string",
                "attendance": "object"
            }
        },
        "check_out": {
            "summary": "Mark attendance check-out",
            "description": "Check out a student from attendance",
            "response": {
                "status": "string",
                "attendance": "object"
            }
        },
        "bulk_checkout": {
            "summary": "Bulk check out attendance",
            "description": "Check out multiple attendance records at once",
            "request_body": {
                "attendance_ids": "array of integers (1-100 items)"
            }
        },
        "pending_checkout": {
            "summary": "Get pending checkout records",
            "description": "List all attendance records that are checked in but not checked out",
            "response": {
                "pending_count": "integer",
                "records": "array of attendance objects"
            }
        },
        "daily_summary": {
            "summary": "Get daily attendance summary",
            "description": "Get attendance statistics for a specific date",
            "parameters": [
                {
                    "name": "date",
                    "description": "Date (YYYY-MM-DD format)",
                    "schema": {"type": "string"}
                }
            ]
        }
    }
}

# Error Response Documentation
ERROR_RESPONSES = {
    "400_bad_request": {
        "description": "Invalid request parameters or validation error",
        "example": {
            "detail": "Invalid page size. Must be between 1 and 200.",
            "error_code": "VALIDATION_ERROR"
        }
    },
    "401_unauthorized": {
        "description": "Authentication required",
        "example": {
            "detail": "Authentication credentials were not provided."
        }
    },
    "403_forbidden": {
        "description": "Insufficient permissions",
        "example": {
            "detail": "You do not have permission to perform this action."
        }
    },
    "404_not_found": {
        "description": "Resource not found",
        "example": {
            "detail": "Not found."
        }
    },
    "429_too_many_requests": {
        "description": "Rate limit exceeded",
        "example": {
            "detail": "Request was throttled. Expected available in 60 seconds."
        }
    }
}

# Common Query Parameters Documentation
COMMON_PARAMETERS = {
    "pagination": {
        "page": {
            "type": "integer",
            "description": "Page number (1-indexed)",
            "example": 1
        },
        "page_size": {
            "type": "integer",
            "description": "Items per page (default: 20, max: 100)",
            "example": 20
        },
        "offset": {
            "type": "integer",
            "description": "Number of items to skip",
            "example": 0
        },
        "limit": {
            "type": "integer",
            "description": "Items to return (default: 50, max: 200)",
            "example": 50
        }
    },
    "filtering": {
        "search": {
            "type": "string",
            "description": "Multi-field search",
            "example": "john"
        },
        "ordering": {
            "type": "string",
            "description": "Field to order by, prefix with '-' for descending",
            "example": "-created_at"
        }
    }
}

# API Usage Examples
API_EXAMPLES = {
    "list_students_paginated": {
        "description": "Get first 20 students",
        "method": "GET",
        "url": "/api/students/?page=1&page_size=20"
    },
    "filter_authorized_students": {
        "description": "Get all authorized students",
        "method": "GET",
        "url": "/api/students/?authorized=true"
    },
    "search_student": {
        "description": "Search for students by name",
        "method": "GET",
        "url": "/api/students/?search=john&ordering=name"
    },
    "bulk_authorize": {
        "description": "Authorize multiple students",
        "method": "POST",
        "url": "/api/students/bulk_authorize/",
        "body": {
            "student_ids": [1, 2, 3, 4, 5]
        }
    },
    "attendance_range": {
        "description": "Get attendance for date range",
        "method": "GET",
        "url": "/api/attendance/?date_from=2026-04-01&date_to=2026-04-20"
    },
    "pending_checkout": {
        "description": "Get students pending checkout",
        "method": "GET",
        "url": "/api/attendance/pending_checkout/"
    },
    "bulk_checkout": {
        "description": "Check out multiple students",
        "method": "POST",
        "url": "/api/attendance/bulk_checkout/",
        "body": {
            "attendance_ids": [10, 11, 12, 13, 14]
        }
    }
}

# Swagger URL Configuration
SWAGGER_URLS = {
    "schema": "/api/schema/",
    "swagger": "/api/docs/",
    "redoc": "/api/redoc/",
}

def get_api_documentation():
    """Get complete API documentation."""
    return {
        "api_info": API_DOCUMENTATION,
        "endpoints": ENDPOINTS_DOCUMENTATION,
        "errors": ERROR_RESPONSES,
        "common_parameters": COMMON_PARAMETERS,
        "examples": API_EXAMPLES,
        "urls": SWAGGER_URLS
    }

logger.info("Swagger/OpenAPI documentation configured")
