"""
Database Initialization Script

Creates database tables and optionally seeds initial data.
"""
import logging
from pathlib import Path

from app import app, db
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database."""
    with app.app_context():
        logger.info('Initializing database...')
        
        # Ensure directories exist
        Config.ensure_directories()
        
        # Create all tables
        db.create_all()
        logger.info('Database tables created successfully')
        
        # Print database info
        if Config.is_sqlite():
            logger.info(f'Using SQLite database at: {Config.DATABASE_PATH}')
        elif Config.is_postgres():
            logger.info(f'Using PostgreSQL database')
        
        logger.info('Database initialization complete')


if __name__ == '__main__':
    init_database()
