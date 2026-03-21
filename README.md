# AI Attendance System using Face Recognition

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org)
[![Django](https://img.shields.io/badge/Django-5.0+-green)](https://www.djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.14+-red)](https://www.django-rest-framework.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A production-ready Django-based AI attendance system that uses advanced face recognition to automatically mark student attendance with comprehensive analytics, reporting, and API integration.

## Table of Contents

- [Features](#features)
- [Technologies](#technologies)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Dashboard & Analytics](#dashboard--analytics)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### ✅ Core Features

- **Face Recognition Engine**
  - Real-time face detection using MTCNN
  - Face encoding with InceptionResnetV1 (VGGFace2)
  - Support for multiple cameras (webcam & IP cameras)
  - Configurable recognition threshold

- **Student Management**
  - Student registration with photo capture
  - Authorized/Unauthorized status management
  - Student profile management
  - Batch import/export functionality

- **Attendance Tracking**
  - Automatic check-in/check-out recognition
  - Time duration calculation
  - Attendance status (present/absent/late)
  - Historical attendance records

### 📊 Analytics & Reporting

- **Dashboard**
  - Real-time attendance statistics
  - Class-wise attendance overview
  - Daily presence/absence visualization
  - Low attendance alerts
  - Customizable date ranges

- **Reports**
  - Monthly attendance summaries
  - Student-wise detailed reports
  - Export to CSV for data analysis
  - Export to PDF for presentations
  - Customizable report generation

### 🔔 Email Notifications

- Automated low attendance alerts
- Weekly attendance reports
- Absence notifications (7+ days)
- Customizable email templates
- Scheduled email tasks via Celery

### 🔌 REST API

- Full RESTful API endpoints
- Token-based authentication
- Filtering, searching, and pagination
- API rate limiting
- Comprehensive API documentation

### 🔒 Security

- Environment-based configuration
- Secure secret key management
- CSRF protection
- CORS support
- SSL/TLS ready
- Role-based access control (RBAC)
- Data validation and sanitization

### ⚡ Performance Optimizations

- Database query optimization
- Redis caching
- Face encoding caching to DB
- Connection pooling
- Pagination for large datasets
- Static file compression (WhiteNoise)

### 🎯 User Experience

- Intuitive dashboard design
- Responsive UI
- Real-time notifications
- User-friendly forms
- Accessible admin panel
- Dark/Light theme support (optional)

---

## Technologies

### Backend
- **Django 5.0** - Web framework
- **Django REST Framework** - API development
- **Celery** - Distributed task queue
- **Redis** - Message broker & caching
- **PostgreSQL** - Production database

### Face Recognition
- **MTCNN** - Multi-task Cascaded CNN for face detection
- **FaceNet** - Face encoding (InceptionResnetV1)
- **PyTorch** - Deep learning framework
- **OpenCV** - Computer vision operations

### Frontend
- **Bootstrap 5** - Responsive CSS framework
- **Chart.js** - Data visualization
- **HTML5/CSS3/JavaScript** - Frontend technologies

### DevOps
- **Docker** - Containerization
- **Gunicorn** - WSGI application server
- **Nginx** - Reverse proxy & web server
- **Let's Encrypt** - SSL/TLS certificates

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+ (or SQLite for development)
- Redis 6.0+
- pip & virtualenv

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/AI-Attendance-System-using-Face-Recognition.git
cd AI-Attendance-System-using-Face-Recognition
```

#### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 5. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

#### 6. Create Superuser

```bash
python manage.py createsuperuser
# Follow the prompts to create admin account
```

#### 7. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

---

## API Documentation

### Authentication

All API endpoints require authentication via token:

```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/v1/students/
```

### Base URL

```
http://localhost:8000/api/v1/
```

### Endpoints

#### Students

```bash
GET    /api/v1/students/                    # List all students
POST   /api/v1/students/                    # Create student
GET    /api/v1/students/{id}/               # Get student details
PUT    /api/v1/students/{id}/               # Update student
DELETE /api/v1/students/{id}/               # Delete student
GET    /api/v1/students/{id}/attendance_details/  # Get attendance
POST   /api/v1/students/{id}/authorize/    # Authorize student
POST   /api/v1/students/{id}/deauthorize/  # Deauthorize student
GET    /api/v1/students/low_attendance/    # List low attendance students
```

#### Attendance

```bash
GET    /api/v1/attendance/                 # List all attendance
GET    /api/v1/attendance/today/           # Today's attendance
GET    /api/v1/attendance/present_today/   # Students present today
GET    /api/v1/attendance/absent_today/    # Students absent today
GET    /api/v1/attendance/date_range/      # Attendance in date range
POST   /api/v1/attendance/bulk_import/     # Bulk import attendance
```

#### Reports

```bash
GET    /api/v1/attendance-summary/              # Attendance summaries
GET    /api/v1/attendance-summary/current_month/
GET    /api/v1/attendance-summary/student_summary/
```

#### Alerts

```bash
GET    /api/v1/alerts/                     # List alerts
GET    /api/v1/alerts/unsent/              # Unsent alerts
POST   /api/v1/alerts/{id}/mark_sent/      # Mark as sent
POST   /api/v1/alerts/send_pending_alerts/ # Send pending
```

### Example Requests

#### Get Students

```bash
curl -X GET "http://localhost:8000/api/v1/students/?authorized=true&student_class=10A" \
  -H "Authorization: Token YOUR_TOKEN"
```

#### Create Attendance

```bash
curl -X POST "http://localhost:8000/api/v1/attendance/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student": 1,
    "date": "2024-01-15",
    "check_in_time": "2024-01-15T08:00:00Z",
    "status": "present"
  }'
```

---

## Dashboard & Analytics

### Dashboard Features

- **Overview Cards**: Total students, present/absent today, total records
- **Charts**: Daily presence trends, class-wise statistics
- **Low Attendance**: Students below threshold with color-coded alerts
- **Quick Actions**: Export to CSV/PDF, view detailed reports

### Create Reports

1. Navigate to `Reports > Attendance Report`
2. Select student and date range
3. Click `Generate Report`
4. Export as CSV or PDF

### Export Attendance

```bash
# Export to CSV
GET /export/attendance/csv/?start_date=2024-01-01&end_date=2024-01-31

# Export to PDF
GET /export/attendance/pdf/?student_id=5
```

---

## Configuration

### Environment Variables

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Redis/Cache
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=noreply@domain.com

# Face Recognition
FACE_RECOGNITION_THRESHOLD=0.6
MIN_ATTENDANCE_THRESHOLD=75
```

### Camera Configuration

1. Go to Admin Panel → Camera Configuration
2. Add camera with:
   - **Name**: Camera location
   - **Source**: `0` for webcam, RTSP URL for IP camera
   - **Threshold**: Recognition confidence (0.4-0.8)

### Email Configuration

1. Update `.env` with email provider credentials
2. Use Gmail App Password (not regular password)
3. Enable "Less secure app access" if needed

---

## Deployment

### Production Deployment

Refer to [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guide covering:

- Nginx + Gunicorn setup
- PostgreSQL configuration
- Redis setup
- Celery task scheduling
- Docker deployment
- SSL/TLS configuration
- Monitoring and logging

### Quick Docker Deployment

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

Access at `http://localhost:8000`

---

## Management Commands

### Update Attendance Summaries

```bash
python manage.py update_attendance_summary --month 2024-01
```

### Send Email Alerts

```bash
python manage.py send_low_attendance_alerts
```

### Check Absent Students

```bash
python manage.py check_absent_students
```

---

## Background Tasks (Celery)

### Available Tasks

- `send_low_attendance_alerts` - Every 6 hours
- `check_absent_students` - Daily at 8 AM
- `update_attendance_summary` - Every 12 hours
- `send_weekly_report` - Weekly (Monday 9 AM)

### Start Services

```bash
# Worker
celery -A Project101 worker --loglevel=info

# Beat Scheduler
celery -A Project101 beat --loglevel=info

# Flower Monitoring (optional)
celery -A Project101 flower
```

---

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test app1

# With coverage
coverage run --source='.' manage.py test
coverage report
```

---

## Performance Optimization

- ✅ Database query optimization with select_related/prefetch_related
- ✅ Redis caching for frequently accessed data
- ✅ Face encoding cache in database
- ✅ Pagination on all list endpoints
- ✅ Static file compression with WhiteNoise
- ✅ Connection pooling for database
- ✅ Lazy loading of heavy computations

---

## Security Best Practices

- ✅ Environment-based configuration
- ✅ Secure secret key management
- ✅ CSRF & CORS protection
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ Rate limiting on API endpoints
- ✅ Role-based access control
- ✅ HTTPS/SSL enforcement
- ✅ Security headers configuration
- ✅ Input validation and sanitization

---

## Troubleshooting

### Common Issues

**Face not recognized:**
- Adjust `FACE_RECOGNITION_THRESHOLD` (lower = stricter matching)
- Ensure student is authorized
- Check image quality and lighting

**Emails not sending:**
- Verify SMTP credentials in `.env`
- Check email provider settings
- Review Celery logs

**Performance issues:**
- Enable Redis caching
- Run Celery worker
- Optimize images
- Add database indexes

**API rate limiting:**
- Increase `DEFAULT_THROTTLE_RATES` in settings
- Implement custom throttling classes

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

For issues, suggestions, or questions:

- 📧 Email: support@yourdomain.com
- 💬 Create an issue in GitHub
- 📚 Check documentation in DEPLOYMENT.md
- 🐛 Report bugs with detailed information

---

## Acknowledgments

- OpenCV community
- PyTorch & FaceNet creators
- Django & DRF maintainers
- Contributors and testers

---

**Made with ❤️ for education and security**
