#!/bin/bash
# Database backup script

BACKUP_DIR="./backups"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/attendance_db_$BACKUP_DATE.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "Starting database backup..."

# Backup database from Docker container
docker-compose exec -T db pg_dump -U ${DB_USER:-postgres} ${DB_NAME:-attendance_db} > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✓ Database backup created: $BACKUP_FILE"
    echo "Backup size: $(du -h $BACKUP_FILE | cut -f1)"
    
    # Keep only last 10 backups
    BACKUP_COUNT=$(ls -1 $BACKUP_DIR/attendance_db_*.sql 2>/dev/null | wc -l)
    if [ $BACKUP_COUNT -gt 10 ]; then
        echo "Cleaning old backups (keeping last 10)..."
        ls -1t $BACKUP_DIR/attendance_db_*.sql | tail -n +11 | xargs rm
    fi
else
    echo "✗ Database backup failed"
    exit 1
fi
