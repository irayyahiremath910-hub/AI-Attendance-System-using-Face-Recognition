# Security Configuration Guide

## Overview
This document outlines the security configurations implemented in the AI Attendance System for production deployment.

## Security Features

### 1. HTTPS/SSL Configuration
**Status**: Configurable via environment variables

**Configuration**:
```env
SECURE_SSL_REDIRECT=True          # Redirect HTTP to HTTPS
SESSION_COOKIE_SECURE=True        # Send cookies only over HTTPS
CSRF_COOKIE_SECURE=True           # Send CSRF cookies only over HTTPS
```

**Benefits**:
- Encrypts data in transit
- Prevents man-in-the-middle attacks
- Protects user sessions and CSRF tokens

### 2. HTTP Strict Transport Security (HSTS)
**Status**: Enabled by default

**Configuration**:
```
SECURE_HSTS_SECONDS=31536000      # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

**Benefits**:
- Forces HTTPS for all future requests
- Prevents downgrade attacks
- Prevents cookie hijacking

### 3. Cross-Site Scripting (XSS) Protection
**Status**: Enabled

**Features**:
- `SECURE_BROWSER_XSS_FILTER=True` - Browser XSS filter
- `Content-Security-Policy` header - Restricts script sources
- HTTPOnly cookies - JavaScript cannot access cookies

**CSP Example**:
```
default-src 'self'; 
script-src 'self' 'unsafe-inline'; 
style-src 'self' 'unsafe-inline';
```

### 4. Cross-Site Request Forgery (CSRF) Protection
**Status**: Enabled

**Features**:
- CSRF tokens on all forms
- `CSRF_COOKIE_HTTPONLY=True` - JavaScript cannot read CSRF token
- `CSRF_COOKIE_SAMESITE=Strict` - CSRF cookies not sent on cross-site requests

### 5. Session Security
**Configuration**:
```env
SESSION_COOKIE_HTTPONLY=True      # JavaScript cannot access session cookie
SESSION_COOKIE_SECURE=True        # Session cookies only over HTTPS
SESSION_COOKIE_SAMESITE=Strict    # Session cookies not sent cross-site
SESSION_COOKIE_AGE=86400          # 24-hour session timeout
```

### 6. Clickjacking Protection
**Status**: Enabled

**Configuration**:
```
X-FRAME-OPTIONS=DENY              # Cannot be framed by other sites
```

### 7. Content Type Sniffing Protection
**Status**: Enabled

**Header**: `X-Content-Type-Options: nosniff`
- Forces browser to respect declared content type

### 8. Referrer Policy
**Status**: Configured

**Header**: `Referrer-Policy: strict-origin-when-cross-origin`
- Limits referrer information sent to other sites

## Environment Variables for Security

### Production Settings
```env
# HTTPS Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# HSTS Settings
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Security Headers
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY
SECURE_CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';
```

### Development Settings
For development, use:
```env
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

## API Security

### API Key Authentication
**Usage**:
```python
from app1.security_utils import require_api_key

@require_api_key
def my_api_view(request):
    # Only valid API keys can access
    pass
```

**Configuration**:
```env
VALID_API_KEYS=key1,key2,key3
```

### IP Whitelisting
**Configuration**:
```env
IP_WHITELIST=192.168.1.1,10.0.0.0/8
```

## Password Security

### Password Validation
Implement strong password requirements using:
```python
from app1.security_utils import validate_password_strength

is_valid, message = validate_password_strength(password)
```

**Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

## Input Sanitization

### Sanitize User Input
```python
from app1.security_utils import sanitize_input

cleaned_input = sanitize_input(user_input, max_length=1000)
```

**Features**:
- Removes dangerous characters
- Limits length
- Strips whitespace

## Security Headers

The application automatically includes these security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| X-XSS-Protection | 1; mode=block | XSS protection |
| Referrer-Policy | strict-origin-when-cross-origin | Limit referrer info |
| Permissions-Policy | geolocation=(), microphone=(), camera=() | Restrict browser APIs |
| Content-Security-Policy | (configured) | Prevent script injection |

## Security Best Practices

### 1. Environment Variables
- **Never commit** `.env` files to version control
- Use `.env.example` as template
- Regenerate `SECRET_KEY` for each deployment

### 2. HTTPS/SSL
- Always use HTTPS in production
- Obtain SSL certificate from Let's Encrypt or other CA
- Enable HSTS for all subdomains

### 3. Database
- Use strong, randomly generated passwords
- Restrict database access by IP
- Enable encryption at rest if possible

### 4. Secrets Management
- Use environment variables for all secrets
- Rotate API keys regularly
- Use different keys for each environment

### 5. Logging & Monitoring
- Log all authentication attempts
- Monitor for suspicious activities
- Set up alerts for security events

### 6. Dependency Management
- Keep Django and dependencies updated
- Regularly scan for vulnerabilities: `pip check`
- Monitor security advisories

### 7. Access Control
- Implement role-based access control (RBAC)
- Use Django's permission system
- Enforce principle of least privilege

## Production Deployment Checklist

```
✓ SECRET_KEY is random and unique
✓ DEBUG = False
✓ ALLOWED_HOSTS configured correctly
✓ SECURE_SSL_REDIRECT = True
✓ SECURE_HSTS_SECONDS set to appropriate value
✓ SESSION_COOKIE_SECURE = True
✓ CSRF_COOKIE_SECURE = True
✓ All security headers enabled
✓ SSL certificate installed and valid
✓ Database encrypted and backed up
✓ API keys rotated
✓ IP whitelist configured if needed
✓ Logging configured for audit trail
✓ Monitoring and alerting set up
✓ Security headers verified with online tools
```

## Security Verification Tools

### Online Tools
- [Security Headers](https://securityheaders.com/) - Check security headers
- [SSL Labs](https://www.ssllabs.com/ssltest/) - SSL/TLS configuration
- [Mozilla Observatory](https://observatory.mozilla.org/) - Security score
- [OWASP ZAP](https://www.zaproxy.org/) - Vulnerability scanning

### Django Management Commands
```bash
# Check deployment settings
python manage.py check --deploy

# Run security tests
python manage.py test

# Check for vulnerable dependencies
pip check
```

## Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/5.0/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## Support

For security issues:
1. **Do NOT** create public GitHub issues
2. Email: security@yourdomain.com
3. Follow responsible disclosure practices

---

**Last Updated**: May 2026
**Next Review**: After each Django/dependency update
