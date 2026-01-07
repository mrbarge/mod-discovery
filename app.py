"""
ModPlayer - Daily Module Music Discovery

Main Flask application.
"""
import logging
import sys
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from config import Config
from models import db
from routes.api import api_bp
from routes.web import web_bp


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure required directories exist
    config_class.ensure_directories()
    
    # Set up logging
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)  # Enable CORS for API requests
    
    # Register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info('Database tables created')
    
    app.logger.info('ModPlayer application started')
    return app


def setup_logging(app):
    """Configure application logging."""
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (if log directory configured)
    if Config.LOG_DIR:
        Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = Config.LOG_DIR / 'modplayer.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        app.logger.addHandler(file_handler)
    
    # Add console handler
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Set log level for other loggers
    logging.getLogger('services').setLevel(log_level)
    logging.getLogger('routes').setLevel(log_level)
    
    # Suppress some noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)


# Create application instance
app = create_app()


if __name__ == '__main__':
    # Run development server
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
