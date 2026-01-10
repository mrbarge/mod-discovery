"""
Curator Service

Handles generation of daily module selections.
"""
import logging
import random
from datetime import date, datetime, timedelta
from typing import List, Optional

from models import DailySelection, Module, SelectionModule, db
from config import Config
from services.modarchive import modarchive_service

logger = logging.getLogger(__name__)


class CuratorService:
    """Service for curating daily module selections."""
    
    def __init__(self):
        self.preferred_formats = Config.PREFERRED_FORMATS
    
    def get_daily_selection(self, selection_date: Optional[date] = None) -> List[Module]:
        """
        Get or create the module selection for a specific date.
        
        Args:
            selection_date: Date to get selection for (default: today)
            
        Returns:
            List of Module objects
        """
        if selection_date is None:
            selection_date = date.today()
        
        # Check if selection already exists
        selection = DailySelection.query.filter_by(date=selection_date).first()
        
        if selection:
            logger.info(f'Found existing selection for {selection_date}')
            # Return modules sorted by position
            modules = sorted(
                selection.modules,
                key=lambda m: self._get_module_position(selection, m)
            )
            return modules
        
        # Generate new selection
        logger.info(f'Generating new selection for {selection_date}')
        modules = self._generate_selection(selection_date)
        
        if modules:
            self._save_selection(selection_date, modules)
        
        return modules
    
    def _get_module_position(self, selection: DailySelection, module: Module) -> int:
        """Get the position of a module in a selection."""
        sm = SelectionModule.query.filter_by(
            selection_id=selection.id,
            module_id=module.id
        ).first()
        return sm.position if sm else 999
    
    def _generate_selection(self, selection_date: date) -> List[Module]:
        """
        Generate a new module selection based on criteria.

        Selects exactly 5 modules:
        1. Featured module (first unlistened from featured chart)
        2. Recent upload (random from recent uploads)
        3. Top rated (random unlistened from random page 1-50)
        4. Top favourite (random unlistened from random page 1-20)
        5. Random module

        Returns:
            List of Module objects
        """
        selected_modules = []
        selected_ids = set()

        # 1. Get featured module (first unlistened)
        featured_module = self._fetch_featured_unlistened()
        if featured_module:
            selected_modules.append(featured_module)
            selected_ids.add(featured_module.id)
            logger.info(f'Selected featured module: {featured_module.filename}')
        else:
            logger.warning('No unlistened featured module found')

        # 2. Get one recent upload
        recent_modules = self._fetch_and_filter_recent()
        recent_modules = [m for m in recent_modules if m.id not in selected_ids]
        if recent_modules:
            recent_module = random.choice(recent_modules)
            selected_modules.append(recent_module)
            selected_ids.add(recent_module.id)
            logger.info(f'Selected recent module: {recent_module.filename}')
        else:
            logger.warning('No recent modules found with preferred formats')

        # 3. Get one highly-rated module (from random page, unlistened)
        rated_module = self._fetch_rated_unlistened(selected_ids)
        if rated_module:
            selected_modules.append(rated_module)
            selected_ids.add(rated_module.id)
            logger.info(f'Selected highly-rated module: {rated_module.filename}')
        else:
            logger.warning('No unlistened highly-rated modules found')

        # 4. Get one top favourite (from random page, unlistened)
        favourite_module = self._fetch_favourite_unlistened(selected_ids)
        if favourite_module:
            selected_modules.append(favourite_module)
            selected_ids.add(favourite_module.id)
            logger.info(f'Selected top favourite module: {favourite_module.filename}')
        else:
            logger.warning('No unlistened top favourite modules found')

        # 5. Get one random module
        random_modules = self._fetch_and_filter_random(10)  # Get extras
        random_modules = [m for m in random_modules if m.id not in selected_ids]

        if random_modules:
            random_module = random.choice(random_modules)
            selected_modules.append(random_module)
            selected_ids.add(random_module.id)
            logger.info(f'Selected random module: {random_module.filename}')
        else:
            logger.warning('No random modules found')

        # 6. Randomize final order
        random.shuffle(selected_modules)

        logger.info(f'Generated selection with {len(selected_modules)} modules')
        return selected_modules
    
    def _is_listened(self, module_id: int) -> bool:
        """Check if a module has been listened to (has a rating)."""
        from models import UserRating
        return UserRating.query.filter_by(module_id=module_id).first() is not None

    def _fetch_featured_unlistened(self) -> Optional[Module]:
        """Fetch the first unlistened featured module."""
        try:
            featured_data = modarchive_service.fetch_featured()

            # Go through featured modules in order, find first unlistened
            for data in featured_data:
                if not self._is_listened(data['id']):
                    # Check if it matches preferred format
                    if data.get('format', '').lower() in [fmt.lower() for fmt in self.preferred_formats]:
                        module = self._get_or_create_module(data)
                        if module:
                            return module

            return None
        except Exception as e:
            logger.error(f'Error fetching featured module: {e}')
            return None

    def _fetch_rated_unlistened(self, excluded_ids: set) -> Optional[Module]:
        """Fetch an unlistened highly-rated module from a random page."""
        try:
            # Fetch from random page (1-50)
            rated_data = modarchive_service.fetch_top_rated(min_rating=10, max_page=50)
            filtered_data = modarchive_service.filter_by_format(rated_data, self.preferred_formats)

            # Filter out already selected and listened modules
            unlistened = [
                data for data in filtered_data
                if data['id'] not in excluded_ids and not self._is_listened(data['id'])
            ]

            if unlistened:
                # Pick a random one from the page
                selected_data = random.choice(unlistened)
                return self._get_or_create_module(selected_data)

            return None
        except Exception as e:
            logger.error(f'Error fetching rated unlistened module: {e}')
            return None

    def _fetch_favourite_unlistened(self, excluded_ids: set) -> Optional[Module]:
        """Fetch an unlistened top favourite module from a random page."""
        try:
            # Fetch from random page (1-20)
            favourite_data = modarchive_service.fetch_top_favourites(max_page=20)
            filtered_data = modarchive_service.filter_by_format(favourite_data, self.preferred_formats)

            # Filter out already selected and listened modules
            unlistened = [
                data for data in filtered_data
                if data['id'] not in excluded_ids and not self._is_listened(data['id'])
            ]

            if unlistened:
                # Pick a random one from the page
                selected_data = random.choice(unlistened)
                return self._get_or_create_module(selected_data)

            return None
        except Exception as e:
            logger.error(f'Error fetching favourite unlistened module: {e}')
            return None

    def _fetch_and_filter_recent(self) -> List[Module]:
        """Fetch recent uploads and filter by preferred formats."""
        try:
            recent_data = modarchive_service.fetch_recent_uploads(limit=30)
            filtered_data = modarchive_service.filter_by_format(recent_data, self.preferred_formats)
            
            modules = []
            for data in filtered_data:
                module = self._get_or_create_module(data)
                if module:
                    modules.append(module)
            
            return modules
        except Exception as e:
            logger.error(f'Error fetching recent modules: {e}')
            return []
    
    def _fetch_and_filter_random(self, count: int) -> List[Module]:
        """Fetch random modules and filter by preferred formats."""
        try:
            # Fetch more than needed since some might not match preferred formats
            fetch_count = count * 3
            random_data = modarchive_service.fetch_random_modules(count=fetch_count)
            filtered_data = modarchive_service.filter_by_format(random_data, self.preferred_formats)
            
            modules = []
            for data in filtered_data:
                module = self._get_or_create_module(data)
                if module:
                    modules.append(module)
            
            return modules
        except Exception as e:
            logger.error(f'Error fetching random modules: {e}')
            return []
    
    def _get_or_create_module(self, data: dict) -> Optional[Module]:
        """
        Get existing module from database or create new one.
        
        Args:
            data: Module data dictionary from ModArchive service
            
        Returns:
            Module object or None if creation failed
        """
        try:
            module = Module.query.get(data['id'])
            
            if module:
                # Update metadata if needed
                module.cached_at = datetime.utcnow()
            else:
                # Create new module
                module = Module(
                    id=data['id'],
                    filename=data['filename'],
                    title=data.get('title'),
                    artist=data.get('artist'),
                    format=data.get('format'),
                    download_url=data.get('download_url'),
                    modarchive_url=data.get('modarchive_url'),
                    source_type=data.get('source_type'),
                    cached_at=datetime.utcnow()
                )
                db.session.add(module)
            
            return module
        except Exception as e:
            logger.error(f'Error creating module from data {data}: {e}')
            return None
    
    def _save_selection(self, selection_date: date, modules: List[Module]) -> bool:
        """
        Save a daily selection to the database.
        
        Args:
            selection_date: Date of the selection
            modules: List of Module objects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create daily selection
            selection = DailySelection(
                date=selection_date,
                created_at=datetime.utcnow()
            )
            db.session.add(selection)
            db.session.flush()  # Get the ID
            
            # Link modules to selection with positions
            for position, module in enumerate(modules, start=1):
                selection_module = SelectionModule(
                    selection_id=selection.id,
                    module_id=module.id,
                    position=position
                )
                db.session.add(selection_module)
            
            db.session.commit()
            logger.info(f'Saved selection for {selection_date} with {len(modules)} modules')
            return True
            
        except Exception as e:
            logger.error(f'Error saving selection: {e}')
            db.session.rollback()
            return False
    
    def get_history(self, limit: int = 30, offset: int = 0) -> List[dict]:
        """
        Get historical selections with ratings.
        
        Args:
            limit: Maximum number of selections to return
            offset: Offset for pagination
            
        Returns:
            List of selection dictionaries with modules and ratings
        """
        try:
            selections = (
                DailySelection.query
                .order_by(DailySelection.date.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            
            history = []
            for selection in selections:
                modules = sorted(
                    selection.modules,
                    key=lambda m: self._get_module_position(selection, m)
                )
                
                history.append({
                    'date': selection.date.isoformat(),
                    'modules': [m.to_dict(include_rating=True) for m in modules]
                })
            
            return history
        except Exception as e:
            logger.error(f'Error fetching history: {e}')
            return []


# Singleton instance
curator_service = CuratorService()
