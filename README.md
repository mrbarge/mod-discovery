# ModPlayer - Daily Mod Music Discovery

> *MAJOR DISCLAIMER* - If it wasn't already completely obvious, this is an extremely vibe-coded experiment via Claude Code.
> Just putting that out there first and foremost!

A lightweight web-based application for discovering and rating module music files from the Mod Archive. Each day, the app presents a curated selection of 3-5 modules to listen to and rate.

## Overview

ModPlayer provides a daily dose of tracker music from the demoscene. The app automatically curates a fresh selection of modules each day, combining recent uploads, highly-rated classics, and random discoveries. Listen to modules directly in your browser and maintain your personal ratings and notes.

## Features

- 🎵 **Daily Curated Selection** - 3-5 new modules to discover each day
- 📅 **Consistent Daily List** - Same modules throughout the day, fresh list tomorrow
- 🎧 **Built-in Player** - Play MOD, XM, S3M, IT formats directly in the browser
- ⭐ **Personal Ratings** - Rate each module from 1-5 stars
- 📝 **Notes & Comments** - Add optional text comments to your ratings
- 📊 **History** - Review past daily selections and your ratings
- 🎲 **Smart Curation** - Mix of recent uploads, highly-rated, and random modules

## Module Selection Criteria

Each day's selection includes:
- **At least 1 recent upload** - Fresh content from Mod Archive's latest uploads
- **At least 1 highly-rated track** - Modules rated 9+ to ensure quality
- **Random discoveries** - Fill remaining slots with random modules for variety
- **Format preference** - Prioritizes .mod, .it, .xm, .s3m formats

## Tech Stack

- **Backend**: Python 3.11+ with Flask
- **Database**: SQLite (easily upgradable to PostgreSQL)
- **Frontend**: HTML5 + Vanilla JavaScript (lightweight, no frameworks)
- **Module Player**: libopenmpt via WebAssembly (chiptune2.js)
- **HTTP Client**: requests library for Mod Archive API

## Requirements

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/modplayer.git
cd modplayer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Run the application:
```bash
python app.py
```

6. Open http://localhost:5000 in your browser

## Running with Containers

### Option 1: Podman/Docker (Single Container with SQLite)

```bash
# Build the image
podman build -t modplayer:latest .

# Run the container
podman run -d \
  --name modplayer \
  -p 5000:5000 \
  -v modplayer-data:/app/data \
  modplayer:latest

# Access at http://localhost:5000
```

### Option 2: Docker Compose (App + PostgreSQL)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 3: Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n modplayer

# Port forward to access locally
kubectl port-forward -n modplayer service/modplayer 5000:5000
```

See `docs/DEPLOYMENT.md` for detailed container deployment instructions.

## Project Structure

```
modplayer/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models (SQLAlchemy)
├── services/
│   ├── modarchive.py      # Mod Archive API integration
│   ├── curator.py         # Daily module selection logic
│   └── player.py          # Module playback helpers
├── routes/
│   ├── api.py             # API endpoints
│   └── web.py             # Web page routes
├── static/
│   ├── css/
│   │   └── style.css      # Application styles
│   ├── js/
│   │   ├── player.js      # Module player integration
│   │   └── app.js         # Frontend logic
│   └── lib/
│       └── chiptune2.js   # Module player library
├── templates/
│   ├── index.html         # Main page
│   └── history.html       # Ratings history page
├── database.db            # SQLite database (created on init)
├── requirements.txt       # Python dependencies
└── init_db.py            # Database initialization script
```

## Usage

### Daily Module Discovery

1. Visit the homepage each day to see your curated selection
2. Click play on any module to listen
3. Rate modules using the 1-5 star rating system
4. Optionally add comments or notes about the module
5. Ratings are saved automatically

### Viewing History

- Navigate to the History page to see all past selections and your ratings
- Filter by date, rating, or search comments

## Configuration

Edit `config.py` to customize:
- Daily module count (default: 3-5)
- Format preferences
- Database location
- Server port and host

## Database Schema

See `ARCHITECTURE.md` for detailed database schema documentation.

## API Endpoints

- `GET /api/daily` - Get today's module selection
- `GET /api/history` - Get past selections and ratings
- `POST /api/rate` - Submit a rating for a module
- `GET /api/module/:id` - Get module details

## Future Enhancements

This app is designed to be easily extended for:
- Deployment to a cloud server (Heroku, Railway, etc.)
- PostgreSQL database for production use
- User authentication for multi-user support
- Mobile-responsive design improvements
- Progressive Web App (PWA) capabilities
- Social features (sharing ratings, etc.)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [The Mod Archive](https://modarchive.org) - For providing access to the world's largest collection of mod files
- [libopenmpt](https://lib.openmpt.org/libopenmpt/) - For the excellent mod playback library
- [chiptune2.js](https://github.com/deskjet/chiptune2.js) - For WebAssembly mod player
- The demoscene community - For decades of amazing music