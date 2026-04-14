"""
Face Upload & Enrollment API Views
Handles student face image upload, encoding, and recognition setup
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from app1.models import Student
from app1.services.face_recognition import FaceRecognitionService
import logging

logger = logging.getLogger(__name__)


class FaceEnrollmentMixin:
    """Mixin for handling face enrollment operations"""
    
    parser_classes = (MultiPartParser, FormParser)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_face(self, request, pk=None):
        """Upload and encode student face image"""
        try:
            student = self.get_object()
            
            if 'face_image' not in request.FILES:
                return Response(
                    {'error': 'No face_image file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            face_image = request.FILES['face_image']
            
            # Save image to student
            student.image = face_image
            student.save()
            
            # Encode face using service
            service = FaceRecognitionService()
            face_encoding = service.encode_uploaded_images(
                student.image.path,
                use_cache=False
            )
            
            if face_encoding:
                student.face_encoding = face_encoding[0].tolist()
                student.face_recognized = True
                student.save()
                
                logger.info(f"Face enrolled for student {student.id}: {student.name}")
                
                return Response({
                    'success': True,
                    'message': f'Face successfully encoded for {student.name}',
                    'face_recognized': True,
                    'student_id': student.id
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Could not detect face in image. Please try another image.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error enrolling face: {str(e)}")
            return Response(
                {'error': f'Face enrollment failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def face_status(self, request, pk=None):
        """Check face enrollment status"""
        student = self.get_object()
        return Response({
            'student_id': student.id,
            'name': student.name,
            'authorized': student.authorized,
            'face_recognized': student.face_recognized,
            'face_encoding_present': student.face_encoding is not None,
            'ready_for_attendance': student.authorized and student.face_recognized
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def reset_face(self, request, pk=None):
        """Reset face encoding for student"""
        student = self.get_object()
        student.face_encoding = None
        student.face_recognized = False
        student.save()
        
        logger.info(f"Face reset for student {student.id}: {student.name}")
        
        return Response({
            'success': True,
            'message': f'Face encoding reset for {student.name}'
        }, status=status.HTTP_200_OK)
