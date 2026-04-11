import os
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Student, Attendance, CameraConfiguration
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
from django.utils import timezone
import pygame  # Import pygame for playing sounds
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
import threading
import time
import base64
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from .forms import (
    StudentForm,
    CameraConfigurationForm,
    AttendanceFilterForm,
    StudentAuthorizationForm
)
# Day 3: Error Handling & Logging Imports
from .error_handlers import (
    handle_exceptions,
    handle_face_recognition_errors,
    handle_database_operations,
    ErrorContext,
    log_function_call
)
from .exceptions import (
    FaceDetectionException,
    FaceEncodingException,
    InvalidStudentException,
    AttendanceRecordException
)
from .logging_config import (
    get_app_logger,
    get_error_logger,
    get_face_logger,
    get_database_logger
)

# Initialize loggers
app_logger = get_app_logger()
error_logger = get_error_logger()
face_logger = get_face_logger()
database_logger = get_database_logger()


# Initialize MTCNN and InceptionResnetV1
mtcnn = MTCNN(keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# Function to detect and encode faces
@handle_face_recognition_errors
def detect_and_encode(image):
    """
    Detect faces in an image and generate encodings
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        List of face encodings
        
    Raises:
        FaceDetectionException: If face detection fails
        FaceEncodingException: If face encoding fails
    """
    try:
        if image is None or image.size == 0:
            raise FaceDetectionException("Invalid or empty image")
        
        face_logger.debug(f"Detecting faces in image of size {image.shape}")
        
        with torch.no_grad():
            boxes, _ = mtcnn.detect(image)
            if boxes is not None:
                faces = []
                face_logger.info(f"Found {len(boxes)} face(s) in image")
                
                for idx, box in enumerate(boxes):
                    try:
                        face = image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                        if face.size == 0:
                            face_logger.warning(f"Face {idx} has zero size, skipping")
                            continue
                        
                        face = cv2.resize(face, (160, 160))
                        face = np.transpose(face, (2, 0, 1)).astype(np.float32) / 255.0
                        face_tensor = torch.tensor(face).unsqueeze(0)
                        encoding = resnet(face_tensor).detach().numpy().flatten()
                        faces.append(encoding)
                        face_logger.debug(f"Successfully encoded face {idx}")
                    except Exception as e:
                        face_logger.warning(f"Failed to encode face {idx}: {str(e)}")
                        continue
                
                if faces:
                    face_logger.info(f"Successfully encoded {len(faces)} face(s)")
                    return faces
                else:
                    raise FaceEncodingException("No valid faces could be encoded")
            else:
                face_logger.warning("No faces detected in image")
                return []
    except Exception as e:
        error_msg = f"Error in face detection/encoding: {str(e)}"
        face_logger.error(error_msg)
        raise FaceDetectionException(error_msg) from e

# Function to encode uploaded images
@handle_database_operations
@log_function_call(logger=app_logger)
def encode_uploaded_images():
    """
    Encode all authorized student images for face recognition
    
    Returns:
        Tuple of (known_face_encodings list, known_face_names list)
    """
    known_face_encodings = []
    known_face_names = []

    try:
        # Fetch only authorized images
        uploaded_images = Student.objects.filter(authorized=True)
        database_logger.info(f"Found {uploaded_images.count()} authorized student(s)")

        for student in uploaded_images:
            try:
                image_path = os.path.join(settings.MEDIA_ROOT, str(student.image))
                
                if not os.path.exists(image_path):
                    database_logger.warning(f"Image for student {student.name} not found at {image_path}")
                    continue
                
                known_image = cv2.imread(image_path)
                if known_image is None:
                    database_logger.warning(f"Failed to read image for student {student.name}")
                    continue
                
                known_image_rgb = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)
                encodings = detect_and_encode(known_image_rgb)
                
                if encodings:
                    known_face_encodings.extend(encodings)
                    known_face_names.append(student.name)
                    database_logger.info(f"Successfully encoded image for student {student.name}")
            except Exception as e:
                database_logger.error(f"Error encoding image for student {student.name}: {str(e)}")
                continue
        
        database_logger.info(f"Encoding complete: {len(known_face_encodings)} encodings from {len(set(known_face_names))} students")
        return known_face_encodings, known_face_names
    
    except Exception as e:
        error_msg = f"Error in encode_uploaded_images: {str(e)}"
        error_logger.error(error_msg, exc_info=True)
        return [], []

# Function to recognize faces
@handle_face_recognition_errors
@log_function_call(logger=face_logger, level='DEBUG')
def recognize_faces(known_encodings, known_names, test_encodings, threshold=0.6):
    """
    Recognize faces by comparing encodings
    
    Args:
        known_encodings: List of known face encodings
        known_names: List of corresponding student names
        test_encodings: List of test face encodings
        threshold: Distance threshold for face matching (default: 0.6)
        
    Returns:
        List of recognized names
    """
    recognized_names = []
    
    if not known_encodings:
        face_logger.warning("No known encodings provided for face recognition")
        return ['Not Recognized'] * len(test_encodings)
    
    try:
        known_encodings_array = np.array(known_encodings)
        
        for test_idx, test_encoding in enumerate(test_encodings):
            try:
                distances = np.linalg.norm(known_encodings_array - test_encoding, axis=1)
                min_distance_idx = np.argmin(distances)
                min_distance = distances[min_distance_idx]
                
                if min_distance < threshold:
                    recognized_name = known_names[min_distance_idx]
                    recognized_names.append(recognized_name)
                    face_logger.info(f"Face {test_idx} recognized as {recognized_name} (distance: {min_distance:.4f})")
                else:
                    recognized_names.append('Not Recognized')
                    face_logger.debug(f"Face {test_idx} not recognized (distance: {min_distance:.4f})")
            except Exception as e:
                face_logger.error(f"Error recognizing face {test_idx}: {str(e)}")
                recognized_names.append('Not Recognized')
        
        face_logger.info(f"Recognition complete: {len([n for n in recognized_names if n != 'Not Recognized'])}/{len(recognized_names)} faces recognized")
        return recognized_names
    except Exception as e:
        error_msg = f"Error in face recognition: {str(e)}"
        face_logger.error(error_msg, exc_info=True)
        return ['Not Recognized'] * len(test_encodings)

# View for capturing student information and image
def capture_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if image_data is provided from webcam capture
            image_data = request.POST.get('image_data')
            
            if image_data:
                # Decode the base64 image data from webcam
                try:
                    header, encoded = image_data.split(',', 1)
                    image_file = ContentFile(base64.b64decode(encoded), name=f"{form.cleaned_data['name']}.jpg")
                    
                    # Create student with form data
                    student = form.save(commit=False)
                    student.image = image_file
                    student.authorized = False  # Default to False during registration
                    student.save()
                    
                    messages.success(request, f'Student {form.cleaned_data["name"]} registered successfully!')
                    return redirect('selfie_success')
                except Exception as e:
                    messages.error(request, f'Error processing image: {str(e)}')
            else:
                # Use uploaded image file
                student = form.save(commit=False)
                student.authorized = False  # Default to False during registration
                student.save()
                
                messages.success(request, f'Student {form.cleaned_data["name"]} registered successfully!')
                return redirect('selfie_success')
        else:
            # Pass form with errors back to template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StudentForm()

    return render(request, 'capture_student.html', {'form': form})


# Success view after capturing student information and image
def selfie_success(request):
    return render(request, 'selfie_success.html')


# This views for capturing studen faces and recognize
def capture_and_recognize(request):
    stop_events = []  # List to store stop events for each thread
    camera_threads = []  # List to store threads for each camera
    camera_windows = []  # List to store window names
    error_messages = []  # List to capture errors from threads

    def process_frame(cam_config, stop_event):
        """Thread function to capture and process frames for each camera."""
        cap = None
        window_created = False  # Flag to track if the window was created
        try:
            # Check if the camera source is a number (local webcam) or a string (IP camera URL)
            if cam_config.camera_source.isdigit():
                cap = cv2.VideoCapture(int(cam_config.camera_source))  # Use integer index for webcam
            else:
                cap = cv2.VideoCapture(cam_config.camera_source)  # Use string for IP camera URL

            if not cap.isOpened():
                raise Exception(f"Unable to access camera {cam_config.name}.")

            threshold = cam_config.threshold

            # Initialize pygame mixer for sound playback
            pygame.mixer.init()
            success_sound = pygame.mixer.Sound('app1/suc.wav')  # load sound path

            window_name = f'Face Recognition - {cam_config.name}'
            camera_windows.append(window_name)  # Track the window name

            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    print(f"Failed to capture frame for camera: {cam_config.name}")
                    break  # If frame capture fails, break from the loop

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                test_face_encodings = detect_and_encode(frame_rgb)  # Function to detect and encode face in frame

                if test_face_encodings:
                    known_face_encodings, known_face_names = encode_uploaded_images()  # Load known face encodings once
                    if known_face_encodings:
                        names = recognize_faces(np.array(known_face_encodings), known_face_names, test_face_encodings, threshold)

                        for name, box in zip(names, mtcnn.detect(frame_rgb)[0]):
                            if box is not None:
                                (x1, y1, x2, y2) = map(int, box)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                                if name != 'Not Recognized':
                                    students = Student.objects.filter(name=name)
                                    if students.exists():
                                        student = students.first()

                                        # Manage attendance based on check-in and check-out logic
                                        attendance, created = Attendance.objects.get_or_create(student=student, date=datetime.now().date())
                                        if created:
                                            attendance.mark_checked_in()
                                            success_sound.play()
                                            cv2.putText(frame, f"{name}, checked in.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                                        else:
                                            if attendance.check_in_time and not attendance.check_out_time:
                                                if timezone.now() >= attendance.check_in_time + timedelta(seconds=60):
                                                    attendance.mark_checked_out()
                                                    success_sound.play()
                                                    cv2.putText(frame, f"{name}, checked out.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                                                else:
                                                    cv2.putText(frame, f"{name}, checked in.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                                            elif attendance.check_in_time and attendance.check_out_time:
                                                cv2.putText(frame, f"{name}, checked out.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                # Display frame in separate window for each camera
                if not window_created:
                    cv2.namedWindow(window_name)  # Only create window once
                    window_created = True  # Mark window as created
                
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()  # Signal the thread to stop when 'q' is pressed
                    break

        except Exception as e:
            print(f"Error in thread for {cam_config.name}: {e}")
            error_messages.append(str(e))  # Capture error message
        finally:
            if cap is not None:
                cap.release()
            if window_created:
                cv2.destroyWindow(window_name)  # Only destroy if window was created

    try:
        # Get all camera configurations
        cam_configs = CameraConfiguration.objects.all()
        if not cam_configs.exists():
            raise Exception("No camera configurations found. Please configure them in the admin panel.")

        # Create threads for each camera configuration
        for cam_config in cam_configs:
            stop_event = threading.Event()
            stop_events.append(stop_event)

            camera_thread = threading.Thread(target=process_frame, args=(cam_config, stop_event))
            camera_threads.append(camera_thread)
            camera_thread.start()

        # Keep the main thread running while cameras are being processed
        while any(thread.is_alive() for thread in camera_threads):
            time.sleep(1)  # Non-blocking wait, allowing for UI responsiveness

    except Exception as e:
        error_messages.append(str(e))  # Capture the error message
    finally:
        # Ensure all threads are signaled to stop
        for stop_event in stop_events:
            stop_event.set()

        # Ensure all windows are closed in the main thread
        for window in camera_windows:
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) >= 1:  # Check if window exists
                cv2.destroyWindow(window)

    # Check if there are any error messages
    if error_messages:
        # Join all error messages into a single string
        full_error_message = "\n".join(error_messages)
        return render(request, 'error.html', {'error_message': full_error_message})  # Render the error page with message

    return redirect('student_attendance_list')

#this is for showing Attendance list
def student_attendance_list(request):
    form = AttendanceFilterForm(request.GET)
    
    # Get all students initially
    students = Student.objects.all()
    student_attendance_data = []
    
    # Apply filters if form is valid
    if form.is_valid():
        student_filter = form.cleaned_data.get('student')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        status = form.cleaned_data.get('status')
        
        # Filter by specific student if selected
        if student_filter:
            students = students.filter(pk=student_filter.pk)
        
        # Build attendance data with filtering
        for student in students:
            attendance_records = Attendance.objects.filter(student=student)
            
            # Filter by date range
            if date_from:
                attendance_records = attendance_records.filter(date__gte=date_from)
            if date_to:
                attendance_records = attendance_records.filter(date__lte=date_to)
            
            # Filter by status
            if status == 'checked_in':
                attendance_records = attendance_records.filter(check_in_time__isnull=False, check_out_time__isnull=True)
            elif status == 'checked_out':
                attendance_records = attendance_records.filter(check_out_time__isnull=False)
            elif status == 'both':
                attendance_records = attendance_records.filter(check_in_time__isnull=False, check_out_time__isnull=False)
            
            attendance_records = attendance_records.order_by('-date')
            
            # Only add students with matching records
            if attendance_records.exists():
                student_attendance_data.append({
                    'student': student,
                    'attendance_records': attendance_records
                })
    else:
        # Show all attendance data if no filters applied
        for student in students:
            attendance_records = Attendance.objects.filter(student=student).order_by('-date')
            if attendance_records.exists():
                student_attendance_data.append({
                    'student': student,
                    'attendance_records': attendance_records
                })

    context = {
        'form': form,
        'student_attendance_data': student_attendance_data,
    }
    return render(request, 'student_attendance_list.html', context)


def home(request):
    total_students = Student.objects.count()
    total_attendance = Attendance.objects.count()
    total_check_ins = Attendance.objects.filter(check_in_time__isnull=False).count()
    total_check_outs = Attendance.objects.filter(check_out_time__isnull=False).count()
    total_cameras = CameraConfiguration.objects.count()

    context = {
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_check_ins': total_check_ins,
        'total_check_outs': total_check_outs,
        'total_cameras': total_cameras,
    }
    return render(request, 'home.html', context)


# Custom user pass test for admin access
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def student_list(request):
    students = Student.objects.all()
    return render(request, 'student_list.html', {'students': students})

@login_required
@user_passes_test(is_admin)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'student_detail.html', {'student': student})

@login_required
@user_passes_test(is_admin)
def student_authorize(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentAuthorizationForm(request.POST)
        if form.is_valid():
            authorize = form.cleaned_data.get('authorize', False)
            student.authorized = authorize
            student.save()
            
            status = "authorized" if authorize else "unauthorized"
            messages.success(request, f'Student {student.name} has been {status}.')
            return redirect('student-detail', pk=pk)
    else:
        form = StudentAuthorizationForm(initial={'student': student, 'authorize': student.authorized})
    
    return render(request, 'student_authorize.html', {'student': student, 'form': form})

# This views is for Deleting student
@login_required
@user_passes_test(is_admin)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('student-list')  # Redirect to the student list after deletion
    
    return render(request, 'student_delete_confirm.html', {'student': student})


# View function for user login
def user_login(request):
    # Check if the request method is POST, indicating a form submission
    if request.method == 'POST':
        # Retrieve username and password from the submitted form data
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user using the provided credentials
        user = authenticate(request, username=username, password=password)

        # Check if the user was successfully authenticated
        if user is not None:
            # Log the user in by creating a session
            login(request, user)
            # Redirect the user to the student list page after successful login
            return redirect('home')  # Replace 'student-list' with your desired redirect URL after login
        else:
            # If authentication fails, display an error message
            messages.error(request, 'Invalid username or password.')

    # Render the login template for GET requests or if authentication fails
    return render(request, 'login.html')


# This is for user logout
def user_logout(request):
    logout(request)
    return redirect('login')  # Replace 'login' with your desired redirect URL after logout

# Function to handle the creation of a new camera configuration
@login_required
@user_passes_test(is_admin)
def camera_config_create(request):
    if request.method == "POST":
        form = CameraConfigurationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Camera configuration created successfully!')
            return redirect('camera_config_list')
        else:
            # Pass form errors to template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CameraConfigurationForm()

    return render(request, 'camera_config_form.html', {'form': form})


# READ: Function to list all camera configurations
@login_required
@user_passes_test(is_admin)
def camera_config_list(request):
    # Retrieve all CameraConfiguration objects from the database
    configs = CameraConfiguration.objects.all()
    # Render the list template with the retrieved configurations
    return render(request, 'camera_config_list.html', {'configs': configs})


# UPDATE: Function to edit an existing camera configuration
@login_required
@user_passes_test(is_admin)
def camera_config_update(request, pk):
    config = get_object_or_404(CameraConfiguration, pk=pk)

    if request.method == "POST":
        form = CameraConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Camera configuration updated successfully!')
            return redirect('camera_config_list')
        else:
            # Pass form errors to template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CameraConfigurationForm(instance=config)
    
    return render(request, 'camera_config_form.html', {'form': form, 'config': config})


# DELETE: Function to delete a camera configuration
@login_required
@user_passes_test(is_admin)
def camera_config_delete(request, pk):
    # Retrieve the specific configuration by primary key or return a 404 error if not found
    config = get_object_or_404(CameraConfiguration, pk=pk)

    # Check if the request method is POST, indicating confirmation of deletion
    if request.method == "POST":
        # Delete the record from the database
        config.delete()  
        # Redirect to the list of camera configurations after deletion
        return redirect('camera_config_list')

    # Render the delete confirmation template with the configuration data
    return render(request, 'camera_config_delete.html', {'config': config})
