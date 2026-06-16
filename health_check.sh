#!/bin/bash
# Health check script for the application

set -e

WEB_URL="http://localhost:8000/health/"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
MAX_RETRIES=30
RETRY_INTERVAL=2

echo "Checking application health..."
echo ""

# Function to check web service
check_web_health() {
    echo "Checking web application health..."
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -f -s -m 5 http://localhost:8000/health/ > /dev/null 2>&1; then
            echo "✓ Web application is healthy"
            return 0
        fi
        echo "  Attempt $i/$MAX_RETRIES - waiting..."
        sleep $RETRY_INTERVAL
    done
    echo "✗ Web application health check failed"
    return 1
}

# Function to check database connection
check_db_health() {
    echo "Checking database connection..."
    for i in $(seq 1 $MAX_RETRIES); do
        if nc -z -w 2 $DB_HOST $DB_PORT 2>/dev/null; then
            echo "✓ Database is accessible"
            return 0
        fi
        echo "  Attempt $i/$MAX_RETRIES - waiting..."
        sleep $RETRY_INTERVAL
    done
    echo "✗ Database health check failed"
    return 1
}

# Function to check static files
check_static_files() {
    echo "Checking static files..."
    if [ -d "static" ] && [ "$(ls -A static)" ]; then
        echo "✓ Static files are present"
        return 0
    else
        echo "⚠ Static files directory is empty"
        return 0
    fi
}

# Run health checks
if check_db_health && check_web_health && check_static_files; then
    echo ""
    echo "================================"
    echo "✓ All health checks passed!"
    echo "================================"
    exit 0
else
    echo ""
    echo "================================"
    echo "✗ Some health checks failed!"
    echo "================================"
    exit 1
fi
