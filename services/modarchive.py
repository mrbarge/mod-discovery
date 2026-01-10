"""
Mod Archive Service

Handles all communication with The Mod Archive API.
"""
import logging
import random
import re
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import Config

logger = logging.getLogger(__name__)


class ModArchiveService:
    """Service for interacting with The Mod Archive."""
    
    def __init__(self):
        self.base_url = Config.MODARCHIVE_BASE_URL
        self.api_url = Config.MODARCHIVE_API_URL
        self.timeout = Config.REQUEST_TIMEOUT
        self.delay = Config.REQUEST_DELAY
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ModPlayer/1.0 (Personal mod music player)'
        })
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        time.sleep(self.delay)
    
    def _parse_module_entry(self, element) -> Optional[Dict]:
        """
        Parse a module entry from HTML.

        This handles both the newer <li> format and older table-based formats.
        """
        try:
            # Find download link with moduleid
            download_link = element.find('a', href=re.compile(r'downloads\.php\?moduleid=\d+'))
            if not download_link:
                return None

            download_href = download_link['href']

            # Extract module ID from download URL
            module_id_match = re.search(r'moduleid=(\d+)', download_href)
            if not module_id_match:
                return None

            module_id = int(module_id_match.group(1))

            # Extract filename from the fragment (after #)
            # Example: downloads.php?moduleid=212618#wishes.xm
            filename = None
            if '#' in download_href:
                filename = download_href.split('#')[-1]

            if not filename:
                filename = f'module_{module_id}.mod'

            # Extract format from filename extension
            format_match = re.search(r'\.([a-z0-9]{2,4})$', filename.lower())
            file_format = format_match.group(1) if format_match else None

            # Find the module title link (module.php?XXXXXX)
            title_link = element.find('a', href=re.compile(r'module\.php\?\d+'))
            title = title_link.get_text(strip=True) if title_link else None

            # Try to extract artist
            artist = None
            # Look for artist link (member.php?XXXXX)
            artist_link = element.find('a', href=re.compile(r'member\.php\?\d+'))
            if artist_link:
                artist = artist_link.get_text(strip=True)

            # Construct URLs
            download_url = f'{self.api_url}/downloads.php?moduleid={module_id}'
            modarchive_url = f'{self.base_url}/index.php?request=view_by_moduleid&query={module_id}'

            return {
                'id': module_id,
                'filename': filename,
                'title': title,
                'artist': artist,
                'format': file_format,
                'download_url': download_url,
                'modarchive_url': modarchive_url,
            }
        except Exception as e:
            logger.warning(f'Error parsing module entry: {e}')
            return None
    
    def fetch_recent_uploads(self, limit: int = 20) -> List[Dict]:
        """
        Fetch recent module uploads.

        Args:
            limit: Maximum number of modules to return

        Returns:
            List of module metadata dictionaries
        """
        url = f'{self.base_url}/index.php?request=view_actions_uploads'

        try:
            logger.info(f'Fetching recent uploads from {url}')
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find list items containing module entries
            modules = []
            seen_ids = set()
            list_items = soup.find_all('li')

            for item in list_items:
                if len(modules) >= limit:
                    break

                module = self._parse_module_entry(item)
                if module and module['id'] not in seen_ids:
                    module['source_type'] = 'recent'
                    modules.append(module)
                    seen_ids.add(module['id'])

            logger.info(f'Found {len(modules)} recent uploads')
            self._rate_limit()
            return modules

        except Exception as e:
            logger.error(f'Error fetching recent uploads: {e}')
            return []
    
    def fetch_top_rated(self, min_rating: int = 10, max_page: int = 50) -> List[Dict]:
        """
        Fetch highly-rated modules from a random page.

        Args:
            min_rating: Minimum rating (default: 10)
            max_page: Maximum page number to randomly select from (default: 50)

        Returns:
            List of module metadata dictionaries from the random page
        """
        # Pick a random page
        page = random.randint(1, max_page)
        url = f'{self.base_url}/index.php?request=view_by_rating_comments&query={min_rating}&page={page}#mods'

        try:
            logger.info(f'Fetching top-rated modules (>={min_rating}) from page {page}: {url}')
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try both table rows and list items
            modules = []
            seen_ids = set()

            # First try list items (newer format)
            list_items = soup.find_all('li')
            for item in list_items:
                module = self._parse_module_entry(item)
                if module and module['id'] not in seen_ids:
                    module['source_type'] = 'rated'
                    modules.append(module)
                    seen_ids.add(module['id'])

            # If no modules found, try table format (older format)
            if not modules:
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        module = self._parse_module_entry(row)
                        if module and module['id'] not in seen_ids:
                            module['source_type'] = 'rated'
                            modules.append(module)
                            seen_ids.add(module['id'])

                    if modules:
                        break

            logger.info(f'Found {len(modules)} top-rated modules on page {page}')
            self._rate_limit()
            return modules

        except Exception as e:
            logger.error(f'Error fetching top-rated modules: {e}')
            return []
    
    def fetch_featured(self) -> List[Dict]:
        """
        Fetch featured modules from the featured chart.

        Returns:
            List of module metadata dictionaries from the featured chart
        """
        url = f'{self.base_url}/index.php?request=view_chart&query=featured'
        modules = []
        seen_ids = set()
        page = 1

        try:
            logger.info(f'Fetching featured modules from {url}')

            # We may need to check multiple pages to find unlistened modules
            # Start with page 1 and continue if needed
            while True:
                page_url = f'{url}&page={page}' if page > 1 else url
                response = self.session.get(page_url, timeout=self.timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Try both table rows and list items
                page_modules = []

                # First try list items (newer format)
                list_items = soup.find_all('li')
                for item in list_items:
                    module = self._parse_module_entry(item)
                    if module and module['id'] not in seen_ids:
                        module['source_type'] = 'featured'
                        page_modules.append(module)
                        seen_ids.add(module['id'])

                # If no modules found, try table format (older format)
                if not page_modules:
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            module = self._parse_module_entry(row)
                            if module and module['id'] not in seen_ids:
                                module['source_type'] = 'featured'
                                page_modules.append(module)
                                seen_ids.add(module['id'])

                        if page_modules:
                            break

                modules.extend(page_modules)

                # If we found modules on this page, return them
                # The curator will filter for unlistened ones
                if page_modules:
                    logger.info(f'Found {len(modules)} featured modules')
                    self._rate_limit()
                    return modules

                # No more modules found, stop searching
                break

            logger.info(f'Found {len(modules)} featured modules')
            self._rate_limit()
            return modules

        except Exception as e:
            logger.error(f'Error fetching featured modules: {e}')
            return []

    def fetch_top_favourites(self, max_page: int = 20) -> List[Dict]:
        """
        Fetch top favourites from a random page.

        Args:
            max_page: Maximum page number to randomly select from (default: 20)

        Returns:
            List of module metadata dictionaries from the random page
        """
        # Pick a random page
        page = random.randint(1, max_page)
        url = f'{self.base_url}/index.php?request=view_top_favourites&page={page}#mods'

        try:
            logger.info(f'Fetching top favourites from page {page}: {url}')
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try both table rows and list items
            modules = []
            seen_ids = set()

            # First try list items (newer format)
            list_items = soup.find_all('li')
            for item in list_items:
                module = self._parse_module_entry(item)
                if module and module['id'] not in seen_ids:
                    module['source_type'] = 'favourites'
                    modules.append(module)
                    seen_ids.add(module['id'])

            # If no modules found, try table format (older format)
            if not modules:
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        module = self._parse_module_entry(row)
                        if module and module['id'] not in seen_ids:
                            module['source_type'] = 'favourites'
                            modules.append(module)
                            seen_ids.add(module['id'])

                    if modules:
                        break

            logger.info(f'Found {len(modules)} top favourites on page {page}')
            self._rate_limit()
            return modules

        except Exception as e:
            logger.error(f'Error fetching top favourites: {e}')
            return []

    def fetch_random_modules(self, count: int = 5) -> List[Dict]:
        """
        Fetch random modules.

        Args:
            count: Number of random modules to fetch

        Returns:
            List of module metadata dictionaries
        """
        url = f'{self.base_url}/index.php?request=view_random'
        modules = []
        seen_ids = set()

        try:
            logger.info(f'Fetching {count} random modules')

            # Fetch multiple random modules (one per request)
            for i in range(count):
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Try list items first (newer format)
                list_items = soup.find_all('li')
                for item in list_items:
                    module = self._parse_module_entry(item)
                    if module and module['id'] not in seen_ids:
                        module['source_type'] = 'random'
                        modules.append(module)
                        seen_ids.add(module['id'])
                        break

                # If no module found, try table format (older format)
                if len(modules) <= i:
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            module = self._parse_module_entry(row)
                            if module and module['id'] not in seen_ids:
                                module['source_type'] = 'random'
                                modules.append(module)
                                seen_ids.add(module['id'])
                                break
                        if modules and len(modules) > i:
                            break

                if i < count - 1:
                    self._rate_limit()

            logger.info(f'Found {len(modules)} random modules')
            return modules

        except Exception as e:
            logger.error(f'Error fetching random modules: {e}')
            return modules  # Return what we got so far
    
    def get_download_url(self, module_id: int) -> str:
        """
        Get direct download URL for a module.
        
        Args:
            module_id: Mod Archive module ID
            
        Returns:
            Download URL string
        """
        return f'{self.api_url}/downloads.php?moduleid={module_id}'
    
    def filter_by_format(self, modules: List[Dict], preferred_formats: List[str]) -> List[Dict]:
        """
        Filter modules by preferred formats.

        Args:
            modules: List of module dictionaries
            preferred_formats: List of preferred format extensions (e.g., ['mod', 'xm'])

        Returns:
            Filtered list of modules
        """
        filtered = []

        for module in modules:
            module_format = module.get('format')
            if module_format:
                if module_format.lower() in [fmt.lower() for fmt in preferred_formats]:
                    filtered.append(module)

        logger.info(f'Filtered {len(modules)} modules to {len(filtered)} with preferred formats')
        return filtered


# Singleton instance
modarchive_service = ModArchiveService()
