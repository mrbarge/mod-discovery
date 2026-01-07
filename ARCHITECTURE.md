# ModPlayer - Architecture Documentation

This document describes the technical architecture, design decisions, and implementation details of the ModPlayer application.

## System Overview

ModPlayer is a single-user web application that curates and presents a daily selection of module music files from The Mod Archive. The application consists of:

1. **Flask Backend** - Python web server handling API requests and business logic
2. **SQLite Database** - Local data persistence for daily selections and ratings
3. **Web Frontend** - Lightweight HTML/JS interface with integrated mod player
4. **Mod Archive Integration** - Service layer for fetching modules from external API

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Web Browser                      │
│  ┌──────────────────────────────────────────────┐  │
│  │           Frontend (HTML/JS)                 │  │
│  │  - Module Player (chiptune2.js)              │  │
│  │  - Rating Interface                          │  │
│  │  - History Viewer                            │  │
│  └───────────────┬──────────────────────────────┘  │
└──────────────────┼──────────────────────────────────┘
                   │ HTTP/JSON
                   │
┌──────────────────┼──────────────────────────────────┐
│  Flask App       │                                  │
│  ┌───────────────▼──────────────┐                   │
│  │      Routes (api.py)         │                   │
│  │  - GET /api/daily            │                   │
│  │  - POST /api/rate            │                   │
│  │  - GET /api/history          │                   │
│  └───────────────┬──────────────┘                   │
│                  │                                  │
│  ┌───────────────▼──────────────┐                   │
│  │   Services Layer              │                   │
│  │  ┌──────────────────────────┐ │                   │
│  │  │  Curator Service         │ │                   │
│  │  │  - Daily selection logic │ │                   │
│  │  │  - Date management       │ │                   │
│  │  └──────────────────────────┘ │                   │
│  │  ┌──────────────────────────┐ │                   │
│  │  │  ModArchive Service      │ │                   │
│  │  │  - API integration       │ │                   │
│  │  │  - Module fetching       │ │                   │
│  │  └──────────────────────────┘ │                   │
│  └───────────────┬──────────────┘                   │
│                  │                                  │
│  ┌───────────────▼──────────────┐                   │
│  │   Database Layer (SQLAlchemy)│                   │
│  │  - Models.py                 │                   │
│  │  - ORM operations            │                   │
│  └───────────────┬──────────────┘                   │
└──────────────────┼──────────────────────────────────┘
                   │
┌──────────────────▼──────────────┐  ┌──────────────────┐
│      SQLite Database            │  │  Mod Archive API │
│  - daily_selections             │  │  - Recent uploads│
│  - modules                      │  │  - Top rated     │
│  - user_ratings                 │  │  - Random mods   │
└─────────────────────────────────┘  └──────────────────┘
```

## Technology Stack

### Backend
- **Python 3.11+**: Modern Python with type hints
- **Flask 3.0+**: Lightweight WSGI web framework
- **SQLAlchemy 2.0+**: SQL toolkit and ORM
- **Requests**: HTTP library for Mod Archive API calls

### Database
- **SQLite**: Lightweight, file-based database
  - Zero configuration
  - Perfect for single-user local application
  - Easy upgrade path to PostgreSQL for multi-user deployment

### Frontend
- **Vanilla JavaScript**: No framework overhead
- **HTML5**: Modern semantic markup
- **CSS3**: Responsive styling
- **chiptune2.js**: WebAssembly mod player
  - Based on libopenmpt
  - Supports MOD, XM, S3M, IT, and other formats
  - In-browser playback without plugins

## Database Schema

### Tables

#### `daily_selections`
Tracks which modules are selected for each day.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| date | DATE UNIQUE NOT NULL | Selection date (YYYY-MM-DD) |
| created_at | TIMESTAMP | When selection was generated |

#### `modules`
Stores module metadata from Mod Archive.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Mod Archive module ID |
| filename | TEXT NOT NULL | Module filename |
| title | TEXT | Module title/song name |
| artist | TEXT | Artist/composer name |
| format | TEXT | File format (mod, xm, s3m, it) |
| size | INTEGER | File size in bytes |
| download_url | TEXT | Direct download URL |
| modarchive_url | TEXT | Mod Archive page URL |
| date_added | DATE | When added to Mod Archive |
| source_type | TEXT | Selection source (recent/rated/random) |
| cached_at | TIMESTAMP | When module was cached locally |

#### `selection_modules`
Join table linking daily selections to modules.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| selection_id | INTEGER FK | References daily_selections.id |
| module_id | INTEGER FK | References modules.id |
| position | INTEGER | Order in daily list (1-5) |

#### `user_ratings`
Stores user ratings and comments.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| module_id | INTEGER FK | References modules.id |
| rating | INTEGER NOT NULL | Rating 1-5 stars |
| comment | TEXT | Optional user comment |
| rated_at | TIMESTAMP | When rating was submitted |
| updated_at | TIMESTAMP | When rating was last updated |

### Indexes

```sql
CREATE INDEX idx_daily_selections_date ON daily_selections(date);
CREATE INDEX idx_modules_format ON modules(format);
CREATE INDEX idx_modules_source_type ON modules(source_type);
CREATE INDEX idx_selection_modules_selection ON selection_modules(selection_id);
CREATE INDEX idx_selection_modules_module ON selection_modules(module_id);
CREATE INDEX idx_user_ratings_module ON user_ratings(module_id);
CREATE INDEX idx_user_ratings_rating ON user_ratings(rating);
```

## Core Services

### Curator Service (`services/curator.py`)

Responsible for generating daily module selections.

**Key Functions:**

```python
def get_daily_selection(date: datetime.date) -> List[Module]:
    """
    Get or create the module selection for a specific date.
    
    - Checks if selection exists for date
    - If not, generates new selection
    - Returns list of 3-5 modules
    """

def generate_selection() -> List[Module]:
    """
    Generate a new module selection based on criteria:
    
    1. Fetch 1+ recent uploads (format filtered)
    2. Fetch 1+ highly rated modules (9+, format filtered)
    3. Fetch random modules to fill remaining slots
    4. Ensure 3-5 total modules
    5. Avoid duplicates from recent selections
    """

def should_include_format(format: str) -> bool:
    """Check if format is preferred (mod, xm, s3m, it)"""
```

**Selection Algorithm:**

```
1. Determine current date (UTC)
2. Check database for existing selection
3. If exists, return cached selection
4. If not exists:
   a. Fetch recent uploads from Mod Archive
      - Filter by preferred formats
      - Pick 1 random module from results
   b. Fetch highly-rated modules (rating >= 9)
      - Filter by preferred formats  
      - Pick 1 random module from results
   c. Calculate remaining slots (target: 3-5 total)
   d. Fetch random modules to fill slots
      - Filter by preferred formats
      - Exclude already selected modules
   e. Randomize final order
   f. Save to database
5. Return selection
```

### ModArchive Service (`services/modarchive.py`)

Handles all communication with The Mod Archive.

**Key Functions:**

```python
def fetch_recent_uploads(limit: int = 20) -> List[Dict]:
    """
    Fetch recent module uploads.
    
    Endpoint: https://modarchive.org/index.php
    Params: ?request=view_actions_uploads
    
    Returns: List of module metadata dicts
    """

def fetch_top_rated(min_rating: int = 9, limit: int = 50) -> List[Dict]:
    """
    Fetch highly-rated modules.
    
    Endpoint: https://modarchive.org/index.php
    Params: ?request=view_by_rating_comments&query=9
    
    Returns: List of module metadata dicts
    """

def fetch_random_modules(count: int = 5) -> List[Dict]:
    """
    Fetch random modules.
    
    Endpoint: https://modarchive.org/index.php
    Params: ?request=view_random
    
    Returns: List of module metadata dicts
    """

def get_download_url(module_id: int) -> str:
    """
    Construct direct download URL for a module.
    
    Format: https://api.modarchive.org/downloads.php?moduleid=MODULE_ID
    """
```

**API Integration Notes:**

- Mod Archive does not require authentication
- Scraping may be necessary if structured API unavailable
- Implement caching to reduce load on Mod Archive
- Respect robots.txt and rate limits
- Parse HTML responses carefully (structure may change)

### Player Service (`services/player.py`)

Manages module playback and caching.

**Key Functions:**

```python
def get_module_file(module_id: int) -> bytes:
    """
    Download and cache module file.
    
    - Check local cache first
    - Download from Mod Archive if needed
    - Store in local cache directory
    - Return file contents
    """

def clear_old_cache(days: int = 30):
    """Remove cached modules older than specified days"""
```

## API Endpoints

### `GET /api/daily`

Returns today's curated module selection.

**Response:**
```json
{
  "date": "2026-01-05",
  "modules": [
    {
      "id": 123456,
      "title": "Awesome Track",
      "artist": "Cool Composer",
      "filename": "awesome.xm",
      "format": "xm",
      "size": 256000,
      "download_url": "https://api.modarchive.org/downloads.php?moduleid=123456",
      "source_type": "recent",
      "user_rating": null
    },
    // ... more modules
  ]
}
```

### `POST /api/rate`

Submit or update a rating for a module.

**Request:**
```json
{
  "module_id": 123456,
  "rating": 4,
  "comment": "Great chiptune vibes!"
}
```

**Response:**
```json
{
  "success": true,
  "rating": {
    "id": 789,
    "module_id": 123456,
    "rating": 4,
    "comment": "Great chiptune vibes!",
    "rated_at": "2026-01-05T10:30:00Z"
  }
}
```

### `GET /api/history`

Get past selections and ratings.

**Query Parameters:**
- `limit` (default: 30): Number of days to return
- `offset` (default: 0): Pagination offset
- `rated_only` (default: false): Only return days with ratings

**Response:**
```json
{
  "history": [
    {
      "date": "2026-01-05",
      "modules": [
        {
          "id": 123456,
          "title": "Awesome Track",
          "rating": 4,
          "comment": "Great chiptune vibes!"
        },
        // ... more modules
      ]
    },
    // ... more days
  ],
  "total": 30,
  "has_more": false
}
```

### `GET /api/module/:id`

Get detailed information about a specific module.

**Response:**
```json
{
  "id": 123456,
  "title": "Awesome Track",
  "artist": "Cool Composer",
  "filename": "awesome.xm",
  "format": "xm",
  "size": 256000,
  "download_url": "https://api.modarchive.org/downloads.php?moduleid=123456",
  "modarchive_url": "https://modarchive.org/module.php?123456",
  "date_added": "2025-12-20",
  "user_rating": {
    "rating": 4,
    "comment": "Great chiptune vibes!",
    "rated_at": "2026-01-05T10:30:00Z"
  }
}
```

## Frontend Architecture

### Module Player Integration

The frontend uses chiptune2.js for module playback:

```javascript
// Initialize player
const player = new ChiptunePlayer(new ChiptuneAudioContext());

// Load and play module
fetch('/api/module/123456/download')
  .then(response => response.arrayBuffer())
  .then(buffer => {
    player.load(buffer);
    player.play();
  });

// Control playback
player.pause();
player.stop();
player.seek(position);

// Get metadata
const duration = player.duration();
const currentPosition = player.position();
const metadata = player.metadata(); // channels, patterns, etc.
```

### State Management

Simple vanilla JS state management:

```javascript
const AppState = {
  currentDate: null,
  modules: [],
  currentlyPlaying: null,
  userRatings: {},
  
  async loadDailySelection() {
    const response = await fetch('/api/daily');
    const data = await response.json();
    this.currentDate = data.date;
    this.modules = data.modules;
    this.render();
  },
  
  async submitRating(moduleId, rating, comment) {
    const response = await fetch('/api/rate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({module_id: moduleId, rating, comment})
    });
    const result = await response.json();
    this.userRatings[moduleId] = result.rating;
    this.render();
  },
  
  render() {
    // Update DOM with current state
  }
};
```

## Configuration

### `config.py`

```python
import os
from pathlib import Path

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Module selection
    DAILY_MODULE_COUNT_MIN = 3
    DAILY_MODULE_COUNT_MAX = 5
    PREFERRED_FORMATS = ['mod', 'xm', 's3m', 'it']
    MIN_TOP_RATING = 9
    
    # Cache settings
    CACHE_DIR = Path('cache/modules')
    CACHE_MAX_AGE_DAYS = 30
    
    # Mod Archive
    MODARCHIVE_BASE_URL = 'https://modarchive.org'
    MODARCHIVE_API_URL = 'https://api.modarchive.org'
    REQUEST_TIMEOUT = 30
    REQUEST_DELAY = 1.0  # Seconds between requests (be polite)
    
    # Server
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

## Deployment Considerations

### Containerization

The application supports multiple containerization strategies:

#### Single Container (SQLite)
- **Use case**: Simple local development, single-user deployments
- **Database**: SQLite file stored in mounted volume
- **Pros**: Simple, no external dependencies, easy Podman deployment
- **Cons**: Not suitable for high-concurrency multi-user scenarios

#### Multi-Container (PostgreSQL)
- **Use case**: Production deployments, multi-user support
- **Database**: PostgreSQL in separate container
- **Pros**: Better concurrency, scalable, production-ready
- **Cons**: More complex setup, requires orchestration

#### Container Technologies Supported
- **Podman**: Daemonless container engine, rootless support
- **Docker**: Traditional container runtime
- **Kubernetes**: Production orchestration platform
- **Docker Compose**: Local multi-container orchestration

### Container Architecture

```
Single Container (Podman):
┌─────────────────────────────────┐
│     ModPlayer Container         │
│  ┌─────────────────────────┐   │
│  │   Flask Application     │   │
│  └───────────┬─────────────┘   │
│              │                  │
│  ┌───────────▼─────────────┐   │
│  │   SQLite Database       │   │
│  │   (Mounted Volume)      │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
        Port 5000

Multi-Container (Docker Compose/K8s):
┌─────────────────────────────────┐
│     ModPlayer Container         │
│  ┌─────────────────────────┐   │
│  │   Flask Application     │   │
│  └───────────┬─────────────┘   │
└──────────────┼──────────────────┘
               │ Database Connection
┌──────────────▼──────────────────┐
│   PostgreSQL Container          │
│  ┌─────────────────────────┐   │
│  │   PostgreSQL Server     │   │
│  │   (Persistent Volume)   │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

### Environment Variables for Containers

```bash
# Database
DATABASE_URL=sqlite:////app/data/database.db  # Single container
DATABASE_URL=postgresql://user:pass@postgres:5432/modplayer  # Multi-container

# Flask
FLASK_ENV=production
SECRET_KEY=<random-secret-key>

# Module Selection
DAILY_MODULE_COUNT_MIN=3
DAILY_MODULE_COUNT_MAX=5

# Server
PORT=5000
HOST=0.0.0.0
```

### Volume Mounts

**Single Container:**
- `/app/data` - Database and cache storage
- `/app/logs` - Application logs (optional)

**Multi-Container:**
- App Container: `/app/cache` - Module cache
- DB Container: `/var/lib/postgresql/data` - PostgreSQL data

### Health Checks

```bash
# HTTP health check endpoint
GET /health

# Response:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-05T10:30:00Z"
}
```

### Container Deployment Guides

For detailed container deployment instructions, see:
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete guide for Podman, Docker, and Docker Compose
- **[k8s/README.md](k8s/README.md)** - Kubernetes deployment guide

### Local Development
- SQLite database in project directory
- Flask development server
- No authentication needed

### Future Production Deployment
- Migrate to PostgreSQL for better concurrency
- Use production WSGI server (Gunicorn/uWSGI)
- Add user authentication (Flask-Login)
- Implement HTTPS
- Add rate limiting
- Use environment variables for secrets
- Consider CDN for static assets
- Implement proper error logging (Sentry)

### Mobile Considerations
- Responsive CSS design
- Touch-friendly controls
- Offline support (Service Workers)
- Progressive Web App (PWA) manifest
- Optimize for slower connections

## Error Handling

### API Error Responses

All API errors return consistent format:

```json
{
  "error": true,
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {}  // Optional additional context
}
```

### Common Error Scenarios

1. **Mod Archive Unavailable**
   - Retry with exponential backoff
   - Cache last successful selections
   - Display user-friendly message

2. **Invalid Module Data**
   - Log error for investigation
   - Skip problematic module
   - Continue with remaining selections

3. **Database Errors**
   - Rollback transaction
   - Return error to user
   - Log for debugging

## Performance Considerations

### Caching Strategy

1. **Daily Selections**: Cache for 24 hours (regenerate at midnight UTC)
2. **Module Metadata**: Cache indefinitely (rarely changes)
3. **Module Files**: Cache for 30 days (clear old files periodically)
4. **API Responses**: Consider Redis for production deployment

### Database Optimization

- Indexes on frequently queried fields
- Periodic VACUUM for SQLite
- Consider connection pooling for production

### Frontend Optimization

- Lazy load module files (only when played)
- Compress static assets
- Use HTTP/2 server push for critical resources
- Implement service worker for offline support

## Testing Strategy

### Unit Tests
- Service layer functions
- Database models
- Utility functions

### Integration Tests
- API endpoints
- Database operations
- Mod Archive integration

### Frontend Tests
- Module player functionality
- Rating submission
- History navigation

## Security Considerations

### Current (Single-User)
- No authentication needed
- Input validation on all forms
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (template escaping)

### Future (Multi-User)
- User authentication and sessions
- CSRF protection
- Rate limiting per user
- Input sanitization
- Secure password storage (bcrypt)

## Monitoring and Logging

### Logging Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages (e.g., API timeouts)
- **ERROR**: Error messages (handled gracefully)
- **CRITICAL**: Critical errors (application failure)

### Key Metrics to Track
- Daily active users (future)
- Module play counts
- Rating submission rate
- API response times
- Mod Archive API success rate
- Database query performance

## Future Enhancements

### Phase 1: Core Features (Current)
- ✅ Daily module selection
- ✅ Built-in player
- ✅ Personal ratings and comments
- ✅ History view

### Phase 2: Enhanced Discovery
- [ ] Custom filters (genre, artist, era)
- [ ] Similar module recommendations
- [ ] Export ratings to CSV
- [ ] Statistics dashboard (personal listening stats)

### Phase 3: Social Features
- [ ] Multi-user support
- [ ] User profiles
- [ ] Shared playlists
- [ ] Comments and discussions
- [ ] Following other users

### Phase 4: Advanced Features
- [ ] Mobile app (React Native/Flutter)
- [ ] Playlist creation
- [ ] Integration with last.fm for scrobbling
- [ ] AI-powered recommendations
- [ ] Community-curated collections

## Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Mod Archive API](https://modarchive.org/index.php?request=view_api) (if available)
- [chiptune2.js](https://github.com/deskjet/chiptune2.js)

### Module Format References
- [MOD Format](https://en.wikipedia.org/wiki/MOD_(file_format))
- [XM Format](https://en.wikipedia.org/wiki/XM_(file_format))
- [S3M Format](https://en.wikipedia.org/wiki/S3M_(file_format))
- [IT Format](https://en.wikipedia.org/wiki/Impulse_Tracker)

### Demoscene Communities
- [Mod Archive Forums](https://forum.modarchive.org/)
- [Scene.org](https://www.scene.org/)
- [Pouët](https://www.pouet.net/)
