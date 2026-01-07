"""
Player Service

Manages module file downloads and caching.
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

from config import Config
from models import Module

logger = logging.getLogger(__name__)


class PlayerService:
    """Service for managing module files."""
    
    def __init__(self):
        self.cache_dir = Config.CACHE_DIR
        self.cache_max_age = timedelta(days=Config.CACHE_MAX_AGE_DAYS)
        self.timeout = Config.REQUEST_TIMEOUT
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_module_file(self, module: Module) -> Optional[bytes]:
        """
        Download and cache module file.
        
        Args:
            module: Module object
            
        Returns:
            File contents as bytes, or None if download failed
        """
        cache_path = self._get_cache_path(module.id)
        
        # Check if file exists in cache and is recent
        if cache_path.exists():
            file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            if file_age < self.cache_max_age:
                logger.info(f'Loading module {module.id} from cache')
                try:
                    return cache_path.read_bytes()
                except Exception as e:
                    logger.warning(f'Error reading cached file: {e}')
        
        # Download from Mod Archive
        logger.info(f'Downloading module {module.id} from {module.download_url}')
        try:
            response = requests.get(module.download_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Save to cache
            cache_path.write_bytes(response.content)
            logger.info(f'Cached module {module.id} to {cache_path}')
            
            return response.content
            
        except Exception as e:
            logger.error(f'Error downloading module {module.id}: {e}')
            
            # If download fails but we have a cached (even old) version, use it
            if cache_path.exists():
                logger.info(f'Using old cached version for module {module.id}')
                try:
                    return cache_path.read_bytes()
                except Exception as e2:
                    logger.error(f'Error reading old cached file: {e2}')
            
            return None
    
    def _get_cache_path(self, module_id: int) -> Path:
        """Get the cache file path for a module."""
        return self.cache_dir / f'{module_id}.mod'
    
    def clear_old_cache(self, max_age_days: Optional[int] = None):
        """
        Remove cached modules older than specified days.
        
        Args:
            max_age_days: Maximum age in days (default: use config value)
        """
        if max_age_days is None:
            max_age_days = Config.CACHE_MAX_AGE_DAYS
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        deleted_count = 0
        for cache_file in self.cache_dir.glob('*.mod'):
            try:
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_mtime < cutoff:
                    cache_file.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.warning(f'Error deleting cache file {cache_file}: {e}')
        
        logger.info(f'Cleared {deleted_count} old cached modules')
        return deleted_count
    
    def get_cache_stats(self) -> dict:
        """Get statistics about the cache."""
        cache_files = list(self.cache_dir.glob('*.mod'))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'count': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }


# Singleton instance
player_service = PlayerService()
