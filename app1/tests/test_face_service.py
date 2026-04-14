"""
Tests for Face Recognition Service
"""

import pytest
from app1.services.face_recognition import FaceRecognitionService
from app1.models import Student
import logging

logger = logging.getLogger(__name__)


class TestFaceRecognitionService:
    """Test cases for FaceRecognitionService"""

    def test_service_initialization(self):
        """Test FaceRecognitionService initializes correctly"""
        service = FaceRecognitionService()
        assert service is not None

    def test_get_mtcnn_model_caching(self):
        """Test MTCNN model is properly cached"""
        service = FaceRecognitionService()
        mtcnn1 = service._get_mtcnn_model()
        mtcnn2 = service._get_mtcnn_model()
        
        # Both should be the same instance (cached)
        assert id(mtcnn1) == id(mtcnn2)

    def test_get_resnet_model_caching(self):
        """Test ResNet model is properly cached"""
        service = FaceRecognitionService()
        resnet1 = service._get_resnet_model()
        resnet2 = service._get_resnet_model()
        
        # Both should be the same instance (cached)
        assert id(resnet1) == id(resnet2)

    def test_detect_and_encode_with_invalid_image(self):
        """Test face detection with invalid image path"""
        service = FaceRecognitionService()
        encoding = service.detect_and_encode('invalid/path/image.jpg')
        assert encoding is None

    def test_recognize_faces_empty_encodings(self):
        """Test face recognition with empty student encodings"""
        service = FaceRecognitionService()
        recognized = service.recognize_faces(
            face_encoding=[[0.1] * 128],
            threshold=0.6
        )
        assert recognized == []

    def test_service_logger(self):
        """Test service logger is configured"""
        service = FaceRecognitionService()
        # Service should have logger
        assert hasattr(service, 'logger')
        assert service.logger.name == 'app1.services.face_recognition'


class TestFaceEncodingStorage:
    """Test cases for face encoding storage"""

    def test_student_face_encoding_field_jsonfield(self, test_student):
        """Test student face_encoding field stores JSON"""
        test_student.face_encoding = [0.1, 0.2, 0.3, 0.4]
        test_student.save()
        
        # Retrieve and verify
        student = Student.objects.get(id=test_student.id)
        assert student.face_encoding == [0.1, 0.2, 0.3, 0.4]

    def test_student_face_recognized_flag(self, test_student):
        """Test face_recognized flag"""
        test_student.face_recognized = True
        test_student.save()
        
        student = Student.objects.get(id=test_student.id)
        assert student.face_recognized is True

    def test_face_encoding_null_by_default(self, test_student):
        """Test face_encoding is null by default"""
        refreshed = Student.objects.get(id=test_student.id)
        assert refreshed.face_encoding is None
        assert refreshed.face_recognized is False
