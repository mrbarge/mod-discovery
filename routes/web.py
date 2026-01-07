"""
Web Routes

HTML page routes for the ModPlayer application.
"""
import logging
from flask import Blueprint, render_template

logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Main page - daily module selection."""
    return render_template('index.html')


@web_bp.route('/history')
def history():
    """History page - past selections and ratings."""
    return render_template('history.html')


@web_bp.route('/health')
def health():
    """Health check endpoint."""
    from models import db
    from datetime import datetime
    
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        logger.error(f'Health check database error: {e}')
        db_status = 'error'
    
    return {
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
