"""
API Routes

RESTful API endpoints for the ModPlayer application.
"""
import logging
from datetime import date, datetime

from flask import Blueprint, jsonify, request, send_file
from io import BytesIO

from models import Module, UserRating, db
from services.curator import curator_service
from services.player import player_service

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/daily', methods=['GET'])
def get_daily():
    """Get today's module selection."""
    try:
        # Allow querying specific date via query param (for testing/history)
        date_str = request.args.get('date')
        if date_str:
            selection_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selection_date = date.today()
        
        modules = curator_service.get_daily_selection(selection_date)
        
        return jsonify({
            'date': selection_date.isoformat(),
            'modules': [m.to_dict(include_rating=True) for m in modules]
        })
    except Exception as e:
        logger.error(f'Error getting daily selection: {e}')
        return jsonify({
            'error': True,
            'message': 'Failed to get daily selection',
            'code': 'DAILY_SELECTION_ERROR'
        }), 500


@api_bp.route('/module/<int:module_id>', methods=['GET'])
def get_module(module_id: int):
    """Get detailed information about a specific module."""
    try:
        module = Module.query.get_or_404(module_id)
        return jsonify(module.to_dict(include_rating=True))
    except Exception as e:
        logger.error(f'Error getting module {module_id}: {e}')
        return jsonify({
            'error': True,
            'message': 'Module not found',
            'code': 'MODULE_NOT_FOUND'
        }), 404


@api_bp.route('/module/<int:module_id>/download', methods=['GET'])
def download_module(module_id: int):
    """Download a module file."""
    try:
        module = Module.query.get_or_404(module_id)
        
        # Get module file (from cache or download)
        file_data = player_service.get_module_file(module)
        
        if file_data is None:
            return jsonify({
                'error': True,
                'message': 'Failed to download module',
                'code': 'DOWNLOAD_ERROR'
            }), 500
        
        # Return file
        return send_file(
            BytesIO(file_data),
            mimetype='application/octet-stream',
            as_attachment=False,
            download_name=module.filename
        )
    except Exception as e:
        logger.error(f'Error downloading module {module_id}: {e}')
        return jsonify({
            'error': True,
            'message': 'Failed to download module',
            'code': 'DOWNLOAD_ERROR'
        }), 500


@api_bp.route('/rate', methods=['POST'])
def rate_module():
    """Submit or update a rating for a module."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': True,
                'message': 'No data provided',
                'code': 'INVALID_REQUEST'
            }), 400
        
        module_id = data.get('module_id')
        rating = data.get('rating')
        comment = data.get('comment', '').strip() or None
        
        # Validate input
        if not module_id or rating is None:
            return jsonify({
                'error': True,
                'message': 'module_id and rating are required',
                'code': 'INVALID_REQUEST'
            }), 400
        
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({
                'error': True,
                'message': 'rating must be an integer between 1 and 5',
                'code': 'INVALID_RATING'
            }), 400
        
        # Check if module exists
        module = Module.query.get(module_id)
        if not module:
            return jsonify({
                'error': True,
                'message': 'Module not found',
                'code': 'MODULE_NOT_FOUND'
            }), 404
        
        # Check if rating already exists
        user_rating = UserRating.query.filter_by(module_id=module_id).first()
        
        if user_rating:
            # Update existing rating
            user_rating.rating = rating
            user_rating.comment = comment
            user_rating.updated_at = datetime.utcnow()
        else:
            # Create new rating
            user_rating = UserRating(
                module_id=module_id,
                rating=rating,
                comment=comment
            )
            db.session.add(user_rating)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rating': user_rating.to_dict()
        })
        
    except Exception as e:
        logger.error(f'Error saving rating: {e}')
        db.session.rollback()
        return jsonify({
            'error': True,
            'message': 'Failed to save rating',
            'code': 'RATING_ERROR'
        }), 500


@api_bp.route('/history', methods=['GET'])
def get_history():
    """Get past selections and ratings."""
    try:
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        # Validate limits
        limit = min(limit, 100)  # Max 100 per request
        limit = max(limit, 1)
        offset = max(offset, 0)
        
        history = curator_service.get_history(limit=limit, offset=offset)
        
        return jsonify({
            'history': history,
            'limit': limit,
            'offset': offset,
            'has_more': len(history) == limit
        })
        
    except Exception as e:
        logger.error(f'Error getting history: {e}')
        return jsonify({
            'error': True,
            'message': 'Failed to get history',
            'code': 'HISTORY_ERROR'
        }), 500


@api_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics."""
    try:
        stats = player_service.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f'Error getting cache stats: {e}')
        return jsonify({
            'error': True,
            'message': 'Failed to get cache stats',
            'code': 'CACHE_ERROR'
        }), 500


@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear old cached modules."""
    try:
        max_age_days = request.args.get('max_age_days', type=int)
        deleted_count = player_service.clear_old_cache(max_age_days)
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })
    except Exception as e:
        logger.error(f'Error clearing cache: {e}')
        return jsonify({
            'error': True,
            'message': 'Failed to clear cache',
            'code': 'CACHE_ERROR'
        }), 500
