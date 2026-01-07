# ModPlayer Project Structure

Complete file organization of the implemented ModPlayer application.

```
modplayer/
├── app.py                      # Main Flask application entry point
├── config.py                   # Configuration management
├── models.py                   # Database models (SQLAlchemy)
├── init_db.py                  # Database initialization script
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── modarchive.py          # Mod Archive API integration
│   ├── curator.py             # Daily module selection logic
│   └── player.py              # Module file management & caching
│
├── routes/                     # API and web routes
│   ├── __init__.py
│   ├── api.py                 # RESTful API endpoints
│   └── web.py                 # HTML page routes
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html              # Base template with layout
│   ├── index.html             # Main daily selection page
│   └── history.html           # History/ratings page
│
├── static/                     # Frontend assets
│   ├── css/
│   │   └── style.css          # Application styles
│   ├── js/
│   │   ├── app.js             # Main application logic
│   │   ├── history.js         # History page logic
│   │   └── player.js          # Module player integration
│   └── lib/
│       └── README.md          # Instructions for chiptune2.js
│
├── data/                       # SQLite database (created at runtime)
│   └── database.db            # (created by init_db.py)
│
├── cache/                      # Cached module files (created at runtime)
│   └── modules/               # Downloaded .mod files
│
├── logs/                       # Application logs (created at runtime)
│   └── modplayer.log
│
├── k8s/                        # Kubernetes manifests
│   ├── README.md              # K8s deployment guide
│   ├── 00-namespace.yaml      # Namespace definition
│   ├── 01-configmap.yaml      # Configuration
│   ├── 02-secret.yaml         # Secrets (passwords, keys)
│   ├── 03-pvc.yaml            # Persistent volume claims
│   ├── 04-postgres.yaml       # PostgreSQL StatefulSet
│   ├── 05-app.yaml            # ModPlayer Deployment
│   └── 06-ingress.yaml        # Ingress configuration
│
├── Dockerfile                  # Container image definition
├── .dockerignore              # Docker build exclusions
├── docker-compose.yml         # Multi-container orchestration
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore                 # Git exclusions
│
├── README.md                   # Project overview
├── QUICKSTART.md              # Quick setup guide
├── ARCHITECTURE.md            # Technical architecture docs
├── DEPLOYMENT.md              # Container deployment guide
└── PROJECT_STRUCTURE.md       # This file
```

## Key Components

### Backend (Python/Flask)

- **app.py**: Main application factory, configures Flask, registers blueprints
- **config.py**: Centralized configuration from environment variables
- **models.py**: SQLAlchemy ORM models for database tables
- **init_db.py**: Database initialization and table creation

### Services Layer

- **modarchive.py**: Web scraping and API integration with The Mod Archive
- **curator.py**: Daily module selection algorithm and history management
- **player.py**: Module file downloading, caching, and cache management

### API Routes

- **web.py**: HTML page rendering (/, /history, /health)
- **api.py**: RESTful JSON API endpoints

### Frontend

- **templates/**: Jinja2 templates for server-side rendering
- **static/css/**: Responsive CSS with dark theme
- **static/js/**: Vanilla JavaScript (no frameworks)
  - Module player integration with chiptune2.js
  - Rating modal and submission
  - History filtering and search

### Containerization

- **Dockerfile**: Multi-stage build for production containers
- **docker-compose.yml**: Local development with PostgreSQL
- **k8s/**: Complete Kubernetes deployment manifests

## File Counts

- Python files: 8
- HTML templates: 3
- JavaScript files: 3
- CSS files: 1
- Configuration files: 6
- Documentation files: 5
- Kubernetes manifests: 8

## Database Schema

4 tables:
- `daily_selections`: Tracks daily module lists
- `modules`: Module metadata from Mod Archive
- `selection_modules`: Join table (many-to-many)
- `user_ratings`: User ratings and comments

## API Endpoints

- `GET /` - Main page
- `GET /history` - History page
- `GET /health` - Health check
- `GET /api/daily` - Get today's selection
- `GET /api/module/<id>` - Get module details
- `GET /api/module/<id>/download` - Download module file
- `POST /api/rate` - Submit rating
- `GET /api/history` - Get past selections
- `GET /api/cache/stats` - Cache statistics
- `POST /api/cache/clear` - Clear old cache

## Dependencies

### Python (requirements.txt)
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-Cors 4.0.0
- SQLAlchemy 2.0.23
- requests 2.31.0
- beautifulsoup4 4.12.2
- gunicorn 21.2.0
- psycopg2-binary 2.9.9

### JavaScript
- chiptune2.js (external, see static/lib/README.md)

## Runtime Directories

Created automatically on first run:
- `data/` - SQLite database
- `cache/modules/` - Downloaded module files
- `logs/` - Application logs

## Configuration

Environment variables (see .env.example):
- Database connection
- Module selection criteria
- Cache settings
- Server configuration
- Logging options
