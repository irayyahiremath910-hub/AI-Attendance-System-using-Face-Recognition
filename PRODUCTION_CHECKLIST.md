# Production Deployment Checklist

## Pre-Deployment (1-2 weeks before launch)

### Security
- [ ] Generate new `SECRET_KEY` for production
- [ ] Review all environment variables
- [ ] Set `DEBUG = False` in production settings
- [ ] Configure `ALLOWED_HOSTS` with production domains
- [ ] Enable HTTPS/SSL with valid certificate
- [ ] Test SSL configuration with [SSL Labs](https://www.ssllabs.com/)
- [ ] Implement all security headers
- [ ] Review and update CSRF protection settings
- [ ] Test security headers with [Security Headers](https://securityheaders.com/)
- [ ] Enable HSTS with appropriate `max-age`
- [ ] Rotate API keys and credentials
- [ ] Review authentication and authorization logic
- [ ] Implement rate limiting
- [ ] Set up IP whitelisting if needed

### Database
- [ ] Migrate to PostgreSQL (if not already done)
- [ ] Set up database backups
- [ ] Test backup and restore procedures
- [ ] Configure database connection pooling
- [ ] Enable database encryption (if available)
- [ ] Set up database monitoring
- [ ] Create separate database users with minimal privileges
- [ ] Document database access procedures

### Static Files & Media
- [ ] Configure static file collection: `python manage.py collectstatic`
- [ ] Set up cloud storage (AWS S3, Azure Blob, etc.)
- [ ] Configure CDN for static assets
- [ ] Test media upload functionality
- [ ] Implement file upload size limits
- [ ] Test media file serving from cloud storage

### Performance
- [ ] Enable caching (Redis/Memcached)
- [ ] Configure database connection pooling
- [ ] Enable gzip compression
- [ ] Minify CSS and JavaScript
- [ ] Optimize database queries
- [ ] Set up monitoring for slow queries
- [ ] Configure cache headers for static files
- [ ] Test with production-like load

### Testing
- [ ] Run all tests: `python manage.py test`
- [ ] Run security checks: `python manage.py check --deploy`
- [ ] Test database migrations: `python manage.py migrate`
- [ ] Verify all URLs work correctly
- [ ] Test authentication flows
- [ ] Test file uploads
- [ ] Test API endpoints (if applicable)
- [ ] Perform load testing
- [ ] Test error pages (404, 500, etc.)

### Logging & Monitoring
- [ ] Configure application logging
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Configure log aggregation (e.g., ELK, Splunk)
- [ ] Set up performance monitoring
- [ ] Configure alerts for critical issues
- [ ] Set up uptime monitoring
- [ ] Document logging setup

### Deployment Infrastructure
- [ ] Set up Docker/container environment (if using)
- [ ] Configure reverse proxy (Nginx/Apache)
- [ ] Set up load balancer (if needed)
- [ ] Configure auto-scaling (if cloud-based)
- [ ] Set up CI/CD pipeline
- [ ] Test deployment process
- [ ] Document deployment procedures
- [ ] Set up rollback plan

### Domain & SSL
- [ ] Verify domain DNS settings
- [ ] Obtain SSL certificate (Let's Encrypt recommended)
- [ ] Configure certificate auto-renewal
- [ ] Test HTTPS redirection
- [ ] Verify certificate is valid and trusted
- [ ] Set up certificate monitoring

### Documentation
- [ ] Document deployment process
- [ ] Document environment variables
- [ ] Create runbook for common operations
- [ ] Document troubleshooting procedures
- [ ] Create incident response plan
- [ ] Document data backup procedures

---

## Deployment Day

### Pre-Deployment Verification (30 minutes before)
- [ ] Verify all commits are pushed to main branch
- [ ] Confirm database backup is created
- [ ] Verify deployment scripts are ready
- [ ] Test deployment in staging environment
- [ ] Confirm rollback procedure is available
- [ ] Notify team about deployment
- [ ] Disable analytics/monitoring alerts (optional)

### Deployment Steps
1. [ ] Pull latest code from repository
2. [ ] Install dependencies: `pip install -r requirements.txt`
3. [ ] Run migrations: `python manage.py migrate`
4. [ ] Collect static files: `python manage.py collectstatic --noinput`
5. [ ] Clear cache: `python manage.py cache_clear` (if applicable)
6. [ ] Start application server (Gunicorn/uWSGI)
7. [ ] Verify application is running
8. [ ] Run smoke tests

### Post-Deployment Verification (Immediately after)
- [ ] Verify application is accessible
- [ ] Test login functionality
- [ ] Test critical user flows
- [ ] Check error logs for issues
- [ ] Monitor error tracking (Sentry, etc.)
- [ ] Verify database connections are working
- [ ] Test API endpoints (if applicable)
- [ ] Monitor application performance
- [ ] Check CPU and memory usage
- [ ] Verify SSL certificate is valid
- [ ] Test file uploads
- [ ] Verify security headers are present

---

## Post-Deployment (2-4 hours after)

### Monitoring
- [ ] Monitor error logs
- [ ] Monitor application performance metrics
- [ ] Monitor database performance
- [ ] Check for any user-reported issues
- [ ] Monitor API rate limiting
- [ ] Verify all alerts are working

### Validation
- [ ] Perform comprehensive smoke tests
- [ ] Verify all integrations are working
- [ ] Test email notifications (if applicable)
- [ ] Test scheduled tasks/cron jobs (if applicable)
- [ ] Verify backups are working
- [ ] Check security headers with online tool

### Documentation
- [ ] Update deployment log
- [ ] Document any issues encountered
- [ ] Update troubleshooting guide
- [ ] Note any changes from planned deployment

---

## Rollback Plan (if needed)

### Symptoms Requiring Rollback
- [ ] Application crashes/won't start
- [ ] Database connection failures
- [ ] Security issues discovered
- [ ] Critical data loss
- [ ] Performance severely degraded

### Rollback Steps
1. [ ] Stop current application
2. [ ] Restore previous database backup
3. [ ] Revert code to previous version: `git revert <commit>`
4. [ ] Redeploy previous version
5. [ ] Run migrations for previous version
6. [ ] Verify application is working
7. [ ] Notify team and stakeholders
8. [ ] Post-mortem analysis

---

## First Week Post-Deployment

### Monitoring & Support
- [ ] Monitor error rates and performance daily
- [ ] Review user feedback and reports
- [ ] Monitor database growth
- [ ] Check backup completion
- [ ] Monitor third-party integrations
- [ ] Monitor API usage and rate limits

### Performance Analysis
- [ ] Analyze slow query logs
- [ ] Identify performance bottlenecks
- [ ] Optimize database queries if needed
- [ ] Optimize caching strategy
- [ ] Monitor cache hit rates

### Security Audit
- [ ] Run final security scan
- [ ] Verify all security headers
- [ ] Check SSL certificate validity
- [ ] Review access logs
- [ ] Verify authentication is working properly
- [ ] Test account lockout mechanisms

### Documentation Updates
- [ ] Update incident response procedures
- [ ] Document learned lessons
- [ ] Update deployment guide
- [ ] Update troubleshooting guide
- [ ] Create post-mortem if issues occurred

---

## Environment Variables Checklist

### Required for Production
- [ ] `SECRET_KEY` - Unique, random, 50+ characters
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` - Production domain(s)
- [ ] `DB_ENGINE = django.db.backends.postgresql`
- [ ] `DB_NAME` - Production database name
- [ ] `DB_USER` - Database user
- [ ] `DB_PASSWORD` - Strong database password
- [ ] `DB_HOST` - Database host
- [ ] `DB_PORT` - Database port (usually 5432)

### Security Variables
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_BROWSER_XSS_FILTER = True`
- [ ] `X_FRAME_OPTIONS = DENY`

### Email/Communication (if applicable)
- [ ] `EMAIL_HOST`
- [ ] `EMAIL_PORT`
- [ ] `EMAIL_HOST_USER`
- [ ] `EMAIL_HOST_PASSWORD`

### Cloud Storage (if applicable)
- [ ] `USE_S3 = True`
- [ ] `AWS_ACCESS_KEY_ID`
- [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] `AWS_STORAGE_BUCKET_NAME`
- [ ] `AWS_S3_REGION_NAME`

### Monitoring (if applicable)
- [ ] `SENTRY_DSN` - Error tracking
- [ ] `LOG_LEVEL = INFO`

---

## Post-Deployment Monitoring Commands

```bash
# Check application status
python manage.py health_check

# View recent errors
python manage.py tail_logs

# Check database
python manage.py dbshell

# Monitor processes
ps aux | grep python

# Check disk space
df -h

# Monitor system resources
top
htop

# Check application logs
tail -f /var/log/django.log
```

---

## Contact & Escalation

### Primary Contact
- **Name**: [Your Name]
- **Email**: [Your Email]
- **Phone**: [Your Phone]

### Escalation
- **For Critical Issues**: Contact team lead
- **For Security Issues**: Email security@domain.com
- **For Downtime**: Contact infrastructure team

---

**Last Updated**: May 2026
**Next Review**: After each deployment or monthly
