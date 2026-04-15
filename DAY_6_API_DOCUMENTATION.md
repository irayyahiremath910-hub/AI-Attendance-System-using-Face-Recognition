# AI Attendance System - Day 6 API Documentation

## New Features Summary

### 1. Attendance Analytics Service
Comprehensive analytics, metrics, and reporting for attendance data with 10+ analytics endpoints.

### 2. Advanced Search & CSV Export
Full-featured search, filtering, and data export capabilities for attendance and student records.

### 3. Admin Dashboard & Real-Time Monitoring
Real-time system monitoring with KPIs, active sessions, pending actions, and alerts.

### 4. Enhanced Error Handling & Security
Middleware for request logging, error handling, security headers, rate limiting, and audit logging.

---

## API Endpoints Documentation

### Analytics Endpoints

#### Get Main Analytics Dashboard
```
GET /api/analytics/
Permission: IsAdminUser

Response:
{
    "report_date": "2026-04-15",
    "period": { ... },
    "overall_metrics": { ... },
    "department_statistics": [ ... ],
    "daily_trends": [ ... ],
    "peak_hours": [ ... ]
}
```

#### Custom Analytics Report
```
POST /api/analytics/
Permission: IsAdminUser

Request Body:
{
    "start_date": "2026-04-01",
    "end_date": "2026-04-15"
}
```

#### Department Statistics
```
GET /api/analytics/departments/
Permission: IsAuthenticated

Returns statistics grouped by department with attendance rates
```

#### System Health Metrics
```
GET /api/analytics/health/
Permission: IsAuthenticated

Returns: System status, authorization rates, face recognition status
```

#### Attendance Forecast
```
GET /api/analytics/forecast/
Permission: IsAdminUser

Returns: 7-day attendance predictions based on historical patterns
```

#### Individual Student Analytics
```
GET /api/analytics/student/<student_id>/?days=30
Permission: IsAuthenticated

Returns: Student-specific metrics, attendance rate, total hours
```

#### Low Attendance Students
```
GET /api/analytics/low-attendance/?threshold=70&days=30
Permission: IsAdminUser

Returns: Students with attendance below threshold
```

#### Daily Trends Analysis
```
GET /api/analytics/trends/?days=30
Permission: IsAuthenticated

Returns: Day-by-day attendance trends
```

#### Peak Hours Analysis
```
GET /api/analytics/peak-hours/
Permission: IsAuthenticated

Returns: Most common check-in hours
```

---

### Search & Filter Endpoints

#### Advanced Student Search
```
POST /api/search/students/
Permission: IsAuthenticated

Request Body:
{
    "query": "John",
    "filters": {
        "authorized": true,
        "face_recognized": true,
        "department": "CSE",
        "created_after": "2026-04-01"
    }
}

Response:
{
    "results_count": 5,
    "results": [ ... ]
}
```

#### Advanced Attendance Search
```
POST /api/search/attendance/
Permission: IsAuthenticated

Request Body:
{
    "filters": {
        "student_id": 1,
        "date_from": "2026-04-01",
        "date_to": "2026-04-15",
        "status": "checked_out",
        "department": "CSE",
        "min_duration_hours": 8
    }
}
```

#### Search Suggestions
```
GET /api/search/suggestions/?q=john&type=student
Permission: IsAuthenticated

Returns autocomplete suggestions for search
```

#### Available Filters
```
GET /api/search/filters/
Permission: IsAuthenticated

Returns: List of available filter options for UI
```

---

### Export Endpoints

#### Export Data to CSV
```
POST /api/export/
Permission: IsAdminUser

Request Body:
{
    "type": "attendance",  // or "students"
    "filters": { ... }
}

Returns: CSV file download
```

---

### Admin Dashboard Endpoints

#### Dashboard Overview
```
GET /api/dashboard/overview/
Permission: IsAdminUser

Returns:
{
    "timestamp": "2026-04-15T10:30:00",
    "today": { ... },
    "this_week": { ... },
    "this_month": { ... },
    "system_health": { ... }
}
```

#### Active Sessions
```
GET /api/dashboard/active-sessions/
Permission: IsAdminUser

Returns: Students currently checked in with check-in duration
```

#### Recent Activities
```
GET /api/dashboard/activities/?limit=20
Permission: IsAdminUser

Returns: Real-time activity feed of check-ins/check-outs
```

#### Pending Actions
```
GET /api/dashboard/pending-actions/
Permission: IsAdminUser

Returns: Tasks that need admin attention:
- Students needing authorization
- Students without face encoding
- Low attendance alerts
```

#### Key Performance Indicators
```
GET /api/dashboard/kpis/
Permission: IsAdminUser

Returns: KPI cards with metrics and trends:
- Today's Attendance Rate
- Weekly Average Attendance
- Authorization Rate
- Face Recognition Rate
- Total Students
- Total Records
```

#### System Alerts
```
GET /api/dashboard/alerts/
Permission: IsAdminUser

Returns: Critical alerts and warnings
```

#### Complete Dashboard
```
GET /api/dashboard/complete/
Permission: IsAdminUser

Returns: All dashboard data in single request
```

---

## Middleware Features

### Request Logging
All requests are logged with:
- HTTP method, path, status code
- User information
- Response time
- Client IP address

### Error Handling
Comprehensive error handling with:
- Detailed error messages
- Proper HTTP status codes
- Structured JSON responses

### Security Headers
Added security headers:
- X-Frame-Options: DENY (clickjacking prevention)
- X-Content-Type-Options: nosniff (MIME sniffing prevention)
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy

### Rate Limiting
- 100 requests per minute per IP
- Graceful failure with 429 Too Many Requests

### Audit Logging
Sensitive operations are logged:
- /api/students/bulk_authorize/
- /api/students/send_bulk_reminders/
- /admin/

---

## Usage Examples

### Example 1: Get Dashboard Overview
```bash
curl -X GET "http://localhost:8000/api/dashboard/overview/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example 2: Search Students
```bash
curl -X POST "http://localhost:8000/api/search/students/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "John",
    "filters": {
      "authorized": true,
      "department": "CSE"
    }
  }'
```

### Example 3: Export Attendance
```bash
curl -X POST "http://localhost:8000/api/export/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "attendance",
    "filters": {
      "date_from": "2026-04-01",
      "date_to": "2026-04-15"
    }
  }' -o attendance.csv
```

### Example 4: Get Analytics Report
```bash
curl -X GET "http://localhost:8000/api/analytics/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Configuration

### Add Middleware to settings.py
```python
MIDDLEWARE = [
    # ... existing middleware ...
    'app1.middleware.RequestLoggingMiddleware',
    'app1.middleware.ErrorHandlingMiddleware',
    'app1.middleware.SecurityHeadersMiddleware',
    'app1.middleware.RateLimitingMiddleware',
    'app1.middleware.PerformanceMonitoringMiddleware',
    'app1.middleware.AuditLoggingMiddleware',
]
```

### Add URLs to api_urls.py
```python
from app1.analytics_views import *
from app1.search_views import SearchAPIView, ExportAPIView, SearchSuggestionsAPIView
from app1.dashboard_views import *

urlpatterns = [
    # Analytics
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('analytics/departments/', DepartmentAnalyticsView.as_view()),
    path('analytics/health/', SystemHealthView.as_view()),
    path('analytics/forecast/', AttendanceForecastView.as_view()),
    path('analytics/student/<int:student_id>/', StudentAnalyticsDetailView.as_view()),
    path('analytics/low-attendance/', LowAttendanceView.as_view()),
    path('analytics/trends/', AttendanceTrendsView.as_view()),
    path('analytics/peak-hours/', PeakHoursView.as_view()),
    
    # Search & Export
    path('search/students/', SearchAPIView.as_view()),
    path('search/attendance/', SearchAPIView.as_view()),
    path('search/suggestions/', SearchSuggestionsAPIView.as_view()),
    path('export/', ExportAPIView.as_view()),
    
    # Dashboard
    path('dashboard/overview/', DashboardOverviewView.as_view()),
    path('dashboard/active-sessions/', ActiveSessionsView.as_view()),
    path('dashboard/activities/', RecentActivitiesView.as_view()),
    path('dashboard/pending-actions/', PendingActionsView.as_view()),
    path('dashboard/kpis/', KeyPerformanceIndicatorsView.as_view()),
    path('dashboard/alerts/', AdminAlertsView.as_view()),
    path('dashboard/complete/', CompleteDashboardView.as_view()),
]
```

---

## Data Flow

```
Request → RequestLoggingMiddleware → AuditLoggingMiddleware →
SecurityHeadersMiddleware → PerformanceMonitoringMiddleware →
RateLimitingMiddleware → ValidationMiddleware →
API Endpoint → Service Layer → Database

Response → ErrorHandlingMiddleware → SecurityHeadersMiddleware →
RequestLoggingMiddleware → Client
```

---

## Performance Considerations

1. **Caching**: Analytics queries are cached for 5 minutes
2. **Database**: Queries use select_related/prefetch_related for optimization
3. **Pagination**: Large result sets are paginated
4. **Rate Limiting**: Prevents abuse with 100 req/min limit
5. **Slow Request Logging**: Requests >1s are logged as warnings

---

## Security Considerations

1. **Authentication**: All endpoints require authentication
2. **Authorization**: Admin endpoints require IsAdminUser permission
3. **CORS**: Enabled for specified domains only
4. **Rate Limiting**: IP-based rate limiting prevents DDoS
5. **Audit Logging**: Sensitive operations are logged
6. **Security Headers**: Comprehensive security headers added
7. **Input Validation**: All inputs are validated

---

## Future Enhancements

- Real-time WebSocket updates for dashboard
- Advanced reporting with PDF export
- Email report scheduling
- Machine learning predictions
- Custom alert configurations
- Two-factor authentication
- API key management
