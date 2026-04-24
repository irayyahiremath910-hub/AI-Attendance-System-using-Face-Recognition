"""JWT Authentication and Token Management - Day 9

This module implements JWT-based authentication with token refresh,
expiration handling, and secure token management for the REST API.
"""

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with additional user information."""
    
    def validate(self, attrs):
        """Validate and add custom claims to token."""
        data = super().validate(attrs)
        
        # Add custom claims
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        # Add user info to token claims
        access_token['user_id'] = self.user.id
        access_token['email'] = self.user.email
        access_token['username'] = self.user.username
        
        # Add user roles/permissions
        if self.user.is_staff:
            access_token['role'] = 'admin'
        elif self.user.is_superuser:
            access_token['role'] = 'superuser'
        else:
            access_token['role'] = 'user'
        
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'is_staff': self.user.is_staff,
            'role': access_token.get('role'),
        }
        
        logger.info(f"User {self.user.username} obtained JWT token")
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view with enhanced response."""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """Handle token request with enhanced logging."""
        try:
            response = super().post(request, *args, **kwargs)
            logger.info(f"Token obtained successfully for {request.data.get('username')}")
            return response
        except Exception as e:
            logger.warning(f"Token obtain failed: {str(e)}")
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """Custom refresh token serializer."""
    
    def validate(self, attrs):
        """Validate refresh token."""
        data = super().validate(attrs)
        logger.info(f"Token refreshed successfully")
        return data


class TokenManagementService:
    """Service for managing JWT tokens."""
    
    @staticmethod
    def get_tokens_for_user(user):
        """Get access and refresh tokens for a user."""
        refresh = RefreshToken.for_user(user)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }
    
    @staticmethod
    def verify_token(token):
        """Verify a JWT token."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            AccessToken(token)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_user_from_token(token):
        """Extract user from JWT token."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            decoded_token = AccessToken(token)
            user_id = decoded_token.get('user_id')
            return User.objects.get(id=user_id)
        except Exception:
            return None


class TokenBlacklistService:
    """Service for blacklisting tokens on logout."""
    
    # In production, use Redis or database for token blacklist
    _blacklist = set()
    
    @classmethod
    def add_to_blacklist(cls, token):
        """Add token to blacklist."""
        cls._blacklist.add(token)
        logger.info(f"Token added to blacklist")
    
    @classmethod
    def is_blacklisted(cls, token):
        """Check if token is blacklisted."""
        return token in cls._blacklist
    
    @classmethod
    def clear_blacklist(cls):
        """Clear the blacklist (for testing)."""
        cls._blacklist.clear()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout endpoint to blacklist refresh token."""
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Blacklist the refresh token
        TokenBlacklistService.add_to_blacklist(refresh_token)
        
        logger.info(f"User {request.user.username} logged out")
        
        return Response(
            {'detail': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response(
            {'detail': 'Logout failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token_view(request):
    """Verify that the current token is valid."""
    user = request.user
    
    return Response({
        'valid': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
        },
        'timestamp': timezone.now().isoformat()
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Register new user endpoint."""
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Validation
        if not all([username, email, password]):
            return Response(
                {'detail': 'Username, email, and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Get tokens
        tokens = TokenManagementService.get_tokens_for_user(user)
        
        logger.info(f"New user registered: {username}")
        
        return Response(tokens, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response(
            {'detail': 'Registration failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token_view(request):
    """Manually refresh access token."""
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        logger.info(f"Token refreshed for user {request.user.username}")
        
        return Response({
            'access': access_token,
            'refresh': refresh_token,
        })
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return Response(
            {'detail': 'Invalid refresh token'},
            status=status.HTTP_400_BAD_REQUEST
        )


# JWT Configuration for settings.py
JWT_SETTINGS = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': 'your-secret-key-change-in-production',
    'VERIFYING_KEY': None,
    
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}

logger.info("JWT Authentication module initialized")
