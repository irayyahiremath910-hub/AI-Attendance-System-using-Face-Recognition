"""
Database Configuration Module for AI Attendance System

This module handles database configuration for both development and production environments.
Supports SQLite for development and PostgreSQL for production.
"""

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent


def get_database_config():
    """
    Get database configuration based on environment variables.
    
    Returns:
        dict: Database configuration dictionary for Django DATABASES setting
    """
    
    # Get database type from environment (defaults to sqlite3 for development)
    db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')
    
    # SQLite Configuration (Development)
    if db_engine == 'django.db.backends.sqlite3':
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    
    # PostgreSQL Configuration (Production)
    elif db_engine == 'django.db.backends.postgresql':
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='ai_attendance_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
            # Connection pool settings for better performance
            'OPTIONS': {
                'connect_timeout': 10,
                'options': '-c default_transaction_isolation=read_committed'
            }
        }
    
    # Default fallback
    else:
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }


def get_database_info():
    """
    Get human-readable database information for logging/debugging.
    
    Returns:
        dict: Database information without sensitive credentials
    """
    db_config = get_database_config()
    
    info = {
        'engine': db_config.get('ENGINE', 'Unknown'),
        'type': 'SQLite' if 'sqlite3' in db_config.get('ENGINE', '') else 'PostgreSQL',
    }
    
    if db_config.get('NAME'):
        if isinstance(db_config['NAME'], Path):
            info['database'] = str(db_config['NAME'])
        else:
            info['database'] = db_config['NAME']
    
    if db_config.get('HOST'):
        info['host'] = db_config['HOST']
    
    if db_config.get('PORT'):
        info['port'] = db_config['PORT']
    
    return info


# Database connection pool settings for production
DATABASE_CONNECTION_POOL_SIZE = config('DATABASE_CONNECTION_POOL_SIZE', default=10, cast=int)
DATABASE_POOL_TIMEOUT = config('DATABASE_POOL_TIMEOUT', default=30, cast=int)


# Development database settings
DEVELOPMENT_DATABASE = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db_dev.sqlite3',
}


# Production database settings template
PRODUCTION_DATABASE_TEMPLATE = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'ai_attendance_prod_db',
    'USER': 'postgres',
    'PASSWORD': 'set-secure-password',
    'HOST': 'your-db-host.com',
    'PORT': '5432',
    'CONN_MAX_AGE': 600,
}
