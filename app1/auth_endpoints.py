"""Authentication API Endpoints - Day 9

This module provides REST API endpoints for JWT authentication,
including login, logout, token refresh, and user registration.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from app1.auth_jwt import (
    CustomTokenObtainPairView,
    TokenManagementService,
    logout_view,
    verify_token_view,
    register_view
)
import logging

logger = logging.getLogger(__name__)


# URL Configuration for auth endpoints:
# 
# urlpatterns = [
#     path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('api/auth/login/', login_view, name='login'),
#     path('api/auth/logout/', logout_view, name='logout'),
#     path('api/auth/register/', register_view, name='register'),
#     path('api/auth/verify/', verify_token_view, name='verify_token'),
#     path('api/auth/user/', current_user_view, name='current_user'),
# ]


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint - obtain JWT tokens.
    
    POST /api/auth/login/
    {
        "username": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "access": "eyJ...",
        "refresh": "eyJ...",
        "user": {
            "id": 1,
            "username": "user@example.com",
            "email": "user@example.com",
            "is_staff": false,
            "role": "user"
        }
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'detail': 'Username and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            tokens = TokenManagementService.get_tokens_for_user(user)
            logger.info(f"User {username} logged in successfully")
            return Response(tokens, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except User.DoesNotExist:
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """
    Get current authenticated user details.
    
    GET /api/auth/user/
    Headers: Authorization: Bearer <access_token>
    
    Response:
    {
        "id": 1,
        "username": "user@example.com",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_staff": false,
        "is_active": true,
        "date_joined": "2026-04-20T10:00:00Z"
    }
    """
    user = request.user
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined.isoformat()
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_view(request):
    """
    Update current user profile.
    
    PUT /api/auth/user/update/
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "newemail@example.com"
    }
    """
    user = request.user
    
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    
    user.save()
    logger.info(f"User {user.username} profile updated")
    
    return Response({
        'message': 'Profile updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Change user password.
    
    POST /api/auth/change-password/
    {
        "old_password": "currentpassword",
        "new_password": "newpassword",
        "confirm_password": "newpassword"
    }
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    # Validate old password
    if not user.check_password(old_password):
        return Response(
            {'detail': 'Invalid old password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new password
    if new_password != confirm_password:
        return Response(
            {'detail': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'detail': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Change password
    user.set_password(new_password)
    user.save()
    
    logger.info(f"User {user.username} changed password")
    
    return Response({
        'message': 'Password changed successfully'
    })


class TokenValidationView(APIView):
    """API view for token validation."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Validate a token.
        
        POST /api/auth/token/validate/
        {
            "token": "eyJ..."
        }
        """
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'detail': 'Token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_valid = TokenManagementService.verify_token(token)
        
        return Response({
            'valid': is_valid,
            'timestamp': timezone.now().isoformat()
        })


# API Authentication settings for settings.py
AUTH_SETTINGS = {
    "INSTALLED_APPS": [
        # ... other apps
        'rest_framework_simplejwt',
        'channels',
    ],
    
    "REST_FRAMEWORK": {
        "DEFAULT_AUTHENTICATION_CLASSES": (
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        "DEFAULT_PERMISSION_CLASSES": (
            'rest_framework.permissions.IsAuthenticated',
        ),
    },
    
    "SIMPLE_JWT": {
        'ACCESS_TOKEN_LIFETIME': 'timedelta(hours=1)',
        'REFRESH_TOKEN_LIFETIME': 'timedelta(days=7)',
        'ROTATE_REFRESH_TOKENS': True,
        'BLACKLIST_AFTER_ROTATION': True,
        'UPDATE_LAST_LOGIN': True,
        'ALGORITHM': 'HS256',
        'SIGNING_KEY': 'your-secret-key',
    }
}


from django.utils import timezone

logger.info("Authentication API endpoints initialized")
