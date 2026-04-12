"""Face Recognition Service

This service handles all face detection, encoding, and recognition operations.
It provides a centralized and optimized interface for face processing tasks.
"""

import os
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from django.conf import settings
from django.core.cache import cache
from app1.models import Student
import logging

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Service for face detection, encoding, and recognition.
    
    Uses caching to improve performance by avoiding repeated model loading
    and known face encoding computation.
    """

    def __init__(self):
        """Initialize the Face Recognition Service with models."""
        self.mtcnn = self._get_mtcnn()
        self.resnet = self._get_resnet()

    @staticmethod
    def _get_mtcnn():
        """Get MTCNN model from cache or initialize it.
        
        Returns:
            MTCNN: The MTCNN face detection model
        """
        cached = cache.get('mtcnn_model')
        if cached:
            logger.debug("Loading MTCNN from cache")
            return cached

        logger.info("Initializing MTCNN model")
        mtcnn = MTCNN(keep_all=True)
        cache.set('mtcnn_model', mtcnn, timeout=86400)  # Cache for 24 hours
        return mtcnn

    @staticmethod
    def _get_resnet():
        """Get ResNet model from cache or initialize it.
        
        Returns:
            InceptionResnetV1: The ResNet model for face encoding
        """
        cached = cache.get('resnet_model')
        if cached:
            logger.debug("Loading ResNet from cache")
            return cached

        logger.info("Initializing ResNet model")
        resnet = InceptionResnetV1(pretrained='vggface2').eval()
        cache.set('resnet_model', resnet, timeout=86400)  # Cache for 24 hours
        return resnet

    def detect_and_encode(self, image):
        """Detect and encode faces in the given image.
        
        Args:
            image (np.ndarray): RGB image array
            
        Returns:
            list: List of face encodings
        """
        try:
            with torch.no_grad():
                boxes, _ = self.mtcnn.detect(image)
                if boxes is not None:
                    faces = []
                    for box in boxes:
                        face = self._extract_face(image, box)
                        if face is not None:
                            encoding = self._get_encoding(face)
                            faces.append(encoding)
                    return faces
        except Exception as e:
            logger.error(f"Face detection error: {e}", exc_info=True)
        return []

    @staticmethod
    def _extract_face(image, box):
        """Extract face ROI from image using bounding box.
        
        Args:
            image (np.ndarray): RGB image
            box (list): Bounding box coordinates [x1, y1, x2, y2]
            
        Returns:
            np.ndarray: Resized face image or None if extraction fails
        """
        try:
            face = image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
            if face.size == 0:
                return None
            face = cv2.resize(face, (160, 160))
            return face
        except Exception as e:
            logger.warning(f"Face extraction failed: {e}")
            return None

    def _get_encoding(self, face):
        """Get face encoding for the given face image.
        
        Args:
            face (np.ndarray): Face image of size (160, 160)
            
        Returns:
            np.ndarray: Face encoding vector
        """
        try:
            face = np.transpose(face, (2, 0, 1)).astype(np.float32) / 255.0
            face_tensor = torch.tensor(face).unsqueeze(0)
            encoding = self.resnet(face_tensor).detach().numpy().flatten()
            return encoding
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return None

    def encode_uploaded_images(self, use_cache=True):
        """Load and encode images of all authorized students.
        
        Args:
            use_cache (bool): Whether to use cache for known encodings
            
        Returns:
            tuple: (known_face_encodings list, known_face_names list)
        """
        cache_key = 'known_face_encodings'
        
        # Try to get from cache if enabled
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug("Loading known face encodings from cache")
                return cached_data

        logger.info("Computing new face encodings for authorized students")
        known_face_encodings = []
        known_face_names = []

        try:
            # Fetch only authorized images
            authorized_students = Student.objects.filter(authorized=True)

            for student in authorized_students:
                try:
                    image_path = os.path.join(settings.MEDIA_ROOT, str(student.image))
                    if not os.path.exists(image_path):
                        logger.warning(f"Image not found for student {student.name}: {image_path}")
                        continue

                    known_image = cv2.imread(image_path)
                    if known_image is None:
                        logger.warning(f"Failed to read image for student {student.name}")
                        continue

                    known_image_rgb = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)
                    encodings = self.detect_and_encode(known_image_rgb)
                    
                    if encodings:
                        known_face_encodings.extend(encodings)
                        known_face_names.extend([student.name] * len(encodings))
                        logger.debug(f"Encoded {len(encodings)} face(s) for student {student.name}")
                except Exception as e:
                    logger.error(f"Error processing image for student {student.name}: {e}")
                    continue

            # Cache the results
            if known_face_encodings:
                cache.set(cache_key, (known_face_encodings, known_face_names), timeout=3600)  # Cache for 1 hour
                logger.info(f"Cached {len(known_face_encodings)} face encodings")

            return known_face_encodings, known_face_names

        except Exception as e:
            logger.error(f"Error in encode_uploaded_images: {e}", exc_info=True)
            return [], []

    def recognize_faces(self, known_encodings, known_names, test_encodings, threshold=0.6):
        """Recognize faces by comparing test encodings with known encodings.
        
        Args:
            known_encodings (list): List of known face encodings
            known_names (list): List of known face names
            test_encodings (list): List of face encodings to recognize
            threshold (float): Distance threshold for face matching (default: 0.6)
            
        Returns:
            list: List of recognized names
        """
        recognized_names = []
        try:
            if not known_encodings or not known_names:
                logger.warning("No known encodings available for recognition")
                return ['Not Recognized'] * len(test_encodings)

            known_array = np.array(known_encodings)
            
            for test_encoding in test_encodings:
                distances = np.linalg.norm(known_array - test_encoding, axis=1)
                min_distance_idx = np.argmin(distances)
                
                if distances[min_distance_idx] < threshold:
                    recognized_names.append(known_names[min_distance_idx])
                    logger.debug(f"Face recognized as {known_names[min_distance_idx]} with distance {distances[min_distance_idx]:.4f}")
                else:
                    recognized_names.append('Not Recognized')
                    logger.debug(f"Face not recognized (min distance: {distances[min_distance_idx]:.4f})")
        except Exception as e:
            logger.error(f"Error in recognize_faces: {e}", exc_info=True)
            return ['Not Recognized'] * len(test_encodings)

        return recognized_names

    def clear_cache(self):
        """Clear all cached data."""
        cache.delete('mtcnn_model')
        cache.delete('resnet_model')
        cache.delete('known_face_encodings')
        logger.info("Face recognition cache cleared")
