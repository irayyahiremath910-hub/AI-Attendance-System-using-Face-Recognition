"""
Database Utility Functions for AI Attendance System

Provides helper functions for database operations, migrations, and health checks.
"""

import os
from django.core.management import call_command
from django.db import connection, connections
from django.db.utils import OperationalError
from decouple import config


def check_database_connection(database='default'):
    """
    Check if database connection is working.
    
    Args:
        database (str): Database alias to check (default: 'default')
        
    Returns:
        tuple: (is_connected, message)
    """
    try:
        conn = connections[database]
        conn.ensure_connection()
        return True, f"Successfully connected to {database} database"
    except OperationalError as e:
        return False, f"Failed to connect to {database} database: {str(e)}"
    except Exception as e:
        return False, f"Database connection error: {str(e)}"


def run_migrations(app=None, database='default'):
    """
    Run Django migrations.
    
    Args:
        app (str): Specific app to migrate (None for all)
        database (str): Database alias to use
        
    Returns:
        tuple: (success, message)
    """
    try:
        if app:
            call_command('migrate', app, database=database, verbosity=1)
            message = f"Migrations completed for app: {app}"
        else:
            call_command('migrate', database=database, verbosity=1)
            message = "All migrations completed successfully"
        return True, message
    except Exception as e:
        return False, f"Migration error: {str(e)}"


def create_migrations(app):
    """
    Create new migrations for an app.
    
    Args:
        app (str): App name to create migrations for
        
    Returns:
        tuple: (success, message)
    """
    try:
        call_command('makemigrations', app, verbosity=1)
        return True, f"Migrations created for app: {app}"
    except Exception as e:
        return False, f"Failed to create migrations: {str(e)}"


def show_migration_status(database='default'):
    """
    Show migration status for all apps.
    
    Args:
        database (str): Database alias to use
        
    Returns:
        str: Migration status output
    """
    try:
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('showmigrations', database=database, stdout=out)
        return out.getvalue()
    except Exception as e:
        return f"Error getting migration status: {str(e)}"


def get_database_engine():
    """
    Get the current database engine being used.
    
    Returns:
        str: Database engine name (sqlite3, postgresql, mysql, etc.)
    """
    from django.conf import settings
    engine = settings.DATABASES['default'].get('ENGINE', '')
    return engine.split('.')[-1]


def get_database_stats():
    """
    Get database statistics and info.
    
    Returns:
        dict: Database statistics
    """
    from django.db import connection
    from django.conf import settings
    
    db_config = settings.DATABASES['default']
    engine = get_database_engine()
    
    stats = {
        'engine': engine,
        'host': db_config.get('HOST', 'N/A'),
        'port': db_config.get('PORT', 'N/A'),
        'name': db_config.get('NAME', 'N/A'),
        'user': db_config.get('USER', 'N/A'),
    }
    
    # Get connection info
    try:
        with connection.cursor() as cursor:
            if 'postgresql' in engine:
                cursor.execute("SELECT version();")
                stats['version'] = cursor.fetchone()[0] if cursor.fetchone() else 'Unknown'
            elif 'sqlite' in engine:
                cursor.execute("SELECT sqlite_version();")
                stats['version'] = cursor.fetchone()[0] if cursor.fetchone() else 'Unknown'
    except Exception as e:
        stats['version'] = f"Error: {str(e)}"
    
    return stats


def backup_database(backup_path='backups'):
    """
    Backup the current database (SQLite only).
    
    Args:
        backup_path (str): Path to store backups
        
    Returns:
        tuple: (success, message)
    """
    import shutil
    from django.conf import settings
    
    engine = get_database_engine()
    
    if 'sqlite' not in engine:
        return False, "Backup for non-SQLite databases requires specialized tools"
    
    try:
        os.makedirs(backup_path, exist_ok=True)
        
        db_file = settings.DATABASES['default'].get('NAME')
        if not os.path.exists(db_file):
            return False, f"Database file not found: {db_file}"
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_path, f"db_backup_{timestamp}.sqlite3")
        
        shutil.copy2(db_file, backup_file)
        return True, f"Database backed up to: {backup_file}"
    except Exception as e:
        return False, f"Backup error: {str(e)}"


def optimize_database():
    """
    Optimize database performance.
    
    Returns:
        tuple: (success, message)
    """
    engine = get_database_engine()
    
    try:
        with connection.cursor() as cursor:
            if 'postgresql' in engine:
                cursor.execute("VACUUM ANALYZE;")
                return True, "PostgreSQL database optimized (VACUUM ANALYZE)"
            elif 'sqlite' in engine:
                cursor.execute("VACUUM;")
                cursor.execute("ANALYZE;")
                return True, "SQLite database optimized (VACUUM & ANALYZE)"
            else:
                return False, f"Optimization not supported for {engine}"
    except Exception as e:
        return False, f"Optimization error: {str(e)}"


def clear_all_data(confirm=False):
    """
    Clear all data from database (DANGEROUS - use with caution).
    
    Args:
        confirm (bool): Must be True to execute
        
    Returns:
        tuple: (success, message)
    """
    if not confirm:
        return False, "Confirmation required to clear database"
    
    try:
        from django.core.management import call_command
        call_command('flush', interactive=False, verbosity=0)
        return True, "All database data cleared"
    except Exception as e:
        return False, f"Error clearing data: {str(e)}"
