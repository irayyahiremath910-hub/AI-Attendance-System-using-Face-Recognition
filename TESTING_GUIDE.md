# Development & Testing Guide

## Table of Contents

1. [Development Setup](#development-setup)
2. [Running the Application](#running-the-application)
3. [Testing](#testing)
4. [API Testing](#api-testing)
5. [Debugging](#debugging)
6. [Common Issues](#common-issues)

---

## Development Setup

### Prerequisites

- Python 3.11+
- pip & virtualenv
- PostgreSQL 12+ (or SQLite for development)
- Redis 6.0+
- Git

### Installation Steps

#### 1. Windows Setup

```bash
# Clone repository
git clone <repo-url>
cd AI-Attendance-System-using-Face-Recognition

# Run setup script
setup.bat
```

#### 2. Linux/Mac Setup

```bash
# Clone repository
git clone <repo-url>
cd AI-Attendance-System-using-Face-Recognition

# Run setup script
chmod +x setup.sh
./setup.sh
```

#### 3. Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create directories
mkdir -p media logs staticfiles
```

---

## Running the Application

### Development Server

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start development server
python manage.py runserver

# Access at http://localhost:8000
```

### With All Services

#### Terminal 1: Django Development Server

```bash
python manage.py runserver
```

#### Terminal 2: Celery Worker

```bash
celery -A Project101 worker --loglevel=info
```

#### Terminal 3: Celery Beat

```bash
celery -A Project101 beat --loglevel=info
```

#### Terminal 4: Redis Server

```bash
redis-server
```

#### Terminal 5: Flower (Monitoring)

```bash
celery -A Project101 flower
# Access at http://localhost:5555
```

---

## Testing

### Run All Tests

```bash
python manage.py test
```

### Run Specific App Tests

```bash
python manage.py test app1
```

### Run with Coverage

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Run Specific Test Class

```bash
python manage.py test app1.tests.StudentTestCase
```

### Run Specific Test Method

```bash
python manage.py test app1.tests.StudentTestCase.test_create_student
```

### Test with Verbosity

```bash
# Verbosity level 0 (minimal), 1, 2, 3 (maximum)
python manage.py test --verbosity=2
```

### Keep Test Database

```bash
python manage.py test --keepdb app1
```

---

## API Testing

### Using cURL

#### Get Students

```bash
curl -X GET "http://localhost:8000/api/v1/students/" \
  -H "Authorization: Token YOUR_TOKEN"
```

#### Get Student by ID

```bash
curl -X GET "http://localhost:8000/api/v1/students/1/" \
  -H "Authorization: Token YOUR_TOKEN"
```

#### Create Student

```bash
curl -X POST "http://localhost:8000/api/v1/students/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone_number": "1234567890",
    "student_class": "10A"
  }'
```

#### Get Attendance

```bash
curl -X GET "http://localhost:8000/api/v1/attendance/" \
  -H "Authorization: Token YOUR_TOKEN"
```

#### Get Low Attendance Students

```bash
curl -X GET "http://localhost:8000/api/v1/students/low_attendance/?threshold=75" \
  -H "Authorization: Token YOUR_TOKEN"
```

### Using Postman

1. Import API Collection from `/api/postman_collection.json`
2. Set `BASE_URL` to `http://localhost:8000`
3. Set `TOKEN` to your authentication token
4. Run requests

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "YOUR_TOKEN"
headers = {"Authorization": f"Token {TOKEN}"}

# Get students
response = requests.get(f"{BASE_URL}/students/", headers=headers)
print(response.json())

# Create student
data = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone_number": "9876543210",
    "student_class": "10B"
}
response = requests.post(f"{BASE_URL}/students/", json=data, headers=headers)
print(response.json())
```

---

## Debugging

### Enable Debug Toolbar

```bash
pip install django-debug-toolbar
```

Update `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'debug_toolbar',
]

MIDDLEWARE = [
    ...
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = ['127.0.0.1']
```

Update `urls.py`:

```python
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

Access at: http://localhost:8000/__debug__/

### Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or using built-in breakpoint() (Python 3.7+)
breakpoint()
```

Commands:
- `n` - Next line
- `s` - Step into function
- `c` - Continue
- `l` - List current code
- `p variable` - Print variable
- `h` - Help

### Django Shell

```bash
python manage.py shell

# Import models
from app1.models import Student, Attendance

# Query database
students = Student.objects.all()
print(students)

# Create object
student = Student.objects.create(
    name="Test Student",
    email="test@example.com",
    phone_number="1234567890",
    student_class="10A"
)

# Update object
student.name = "Updated Name"
student.save()

# Delete object
student.delete()
```

### View Query Logs

```python
# In Django shell
from django.db import connection
from django.db import reset_queries

reset_queries()

# Run your code
students = Student.objects.all()

# Print queries
print(connection.queries)
```

### Performance Profiling

```bash
pip install django-silk
```

Configure and access profiling data in admin panel.

---

## Common Issues

### 1. "No module named 'X'"

**Solution:**
```bash
pip install -r requirements.txt
```

### 2. Database Migration Error

**Solution:**
```bash
# Check migration status
python manage.py showmigrations

# Revert migrations
python manage.py migrate app1 0001

# Re-migrate
python manage.py migrate
```

### 3. Redis Connection Error

**Solution:**
```bash
# Start Redis
redis-server

# Or check if running
redis-cli ping  # Should respond: PONG
```

### 4. Static Files Not Loading

**Solution:**
```bash
python manage.py collectstatic --clear --noinput
```

### 5. Celery Tasks Not Running

**Solution:**
```bash
# Check Celery worker is running
celery -A Project101 worker --loglevel=debug

# Check Beat scheduler
celery -A Project101 beat --loglevel=debug

# Verify Redis is running
redis-cli ping
```

### 6. Port Already in Use

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Or use different port
python manage.py runserver 8001
```

### 7. Permission Denied on setup.sh

**Solution:**
```bash
chmod +x setup.sh
./setup.sh
```

### 8. CSRF Verification Failed

**Solution:**
```python
# In templates, include CSRF token
{% csrf_token %}

# Or disable for API development (NOT for production)
@csrf_exempt
def my_view(request):
    pass
```

### 9. Face Recognition Not Working

**Solution:**
- Adjust `FACE_RECOGNITION_THRESHOLD` in settings
- Check image quality and lighting
- Verify student is authorized
- Check camera configuration

### 10. Email Not Sending

**Solution:**
```bash
# Test email configuration
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test Message',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False
)
```

---

## Performance Optimization Tips

1. **Enable Caching:**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

2. **Use select_related() & prefetch_related():**
   ```python
   # Instead of
   students = Student.objects.all()
   
   # Use
   students = Student.objects.select_related('attendance_records')
   ```

3. **Add Database Indexes:**
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['authorized', 'name']),
       ]
   ```

4. **Enable Query Caching:**
   ```python
   from django.views.decorators.cache import cache_page
   
   @cache_page(60 * 5)  # Cache for 5 minutes
   def view_function(request):
       pass
   ```

5. **Use Pagination:**
   ```python
   from rest_framework.pagination import PageNumberPagination
   
   class StandardPagination(PageNumberPagination):
       page_size = 10
       page_size_query_param = 'page_size'
       max_page_size = 100
   ```

---

## Useful Commands

```bash
# Create new app
python manage.py startapp myapp

# Create migration
python manage.py makemigrations

# Show migrations
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Change password
python manage.py changepassword username

# Dump data
python manage.py dumpdata > data.json

# Load data
python manage.py loaddata data.json

# Run custom command
python manage.py update_attendance_summary

# Start shell
python manage.py shell

# Run tests
python manage.py test

# Check deployability
python manage.py check --deploy
```

---

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
