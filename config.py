"""
ModPlayer Configuration

Loads configuration from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from typing import List


class Config:
    """Application configuration."""
    
    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'data' / 'database.db'))
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{DATABASE_PATH}'
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    
    # Module selection
    DAILY_MODULE_COUNT = 5  # Fixed at 5 modules per day
    PREFERRED_FORMATS: List[str] = os.getenv(
        'PREFERRED_FORMATS',
        'mod,xm,s3m,it'
    ).split(',')
    
    # Cache settings
    CACHE_DIR = Path(os.getenv('CACHE_DIR', str(BASE_DIR / 'cache' / 'modules')))
    CACHE_MAX_AGE_DAYS = int(os.getenv('CACHE_MAX_AGE_DAYS', '30'))
    
    # Mod Archive
    MODARCHIVE_BASE_URL = 'https://modarchive.org'
    MODARCHIVE_API_URL = 'https://api.modarchive.org'
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1.0'))
    
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = Path(os.getenv('LOG_DIR', str(BASE_DIR / 'logs')))
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        directories = [
            Path(cls.DATABASE_PATH).parent if cls.DATABASE_URL.startswith('sqlite') else None,
            cls.CACHE_DIR,
            cls.LOG_DIR,
        ]
        
        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_sqlite(cls) -> bool:
        """Check if using SQLite database."""
        return cls.DATABASE_URL.startswith('sqlite')
    
    @classmethod
    def is_postgres(cls) -> bool:
        """Check if using PostgreSQL database."""
        return cls.DATABASE_URL.startswith('postgresql')
