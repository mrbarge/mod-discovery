# ModPlayer Quick Start Guide

Get up and running with ModPlayer in minutes!

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git (optional, for cloning)

## Local Development Setup

### 1. Get the Code

```bash
# If you cloned from git
cd modplayer

# Or if you have the files locally
cd /path/to/modplayer
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Configuration (Optional)

For basic local development, the defaults work fine. If you want to customize:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferences
nano .env  # or use your preferred editor
```

### 5. Initialize Database

```bash
python init_db.py
```

You should see:
```
INFO:__main__:Initializing database...
INFO:__main__:Database tables created successfully
INFO:__main__:Using SQLite database at: /path/to/modplayer/data/database.db
INFO:__main__:Database initialization complete
```

### 6. Get chiptune2.js (Optional but Recommended)

For in-browser module playback:

```bash
# Download from GitHub
cd static/lib
wget https://raw.githubusercontent.com/deskjet/chiptune2.js/master/chiptune2.js
# Or manually download and place in static/lib/

cd ../..
```

See `static/lib/README.md` for more options.

### 7. Run the Application

```bash
python app.py
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: off
INFO:werkzeug:WARNING: This is a development server.
INFO:werkzeug: * Running on http://0.0.0.0:5000
INFO:werkzeug:Press CTRL+C to quit
```

### 8. Open in Browser

Visit http://localhost:5000

The first time you visit, the app will fetch modules from Mod Archive (this may take a few seconds).

## Testing the Application

### Manual Testing

1. **Check Daily Selection**
   - Visit http://localhost:5000
   - You should see 3-5 modules listed
   - Try clicking "Play" on a module
   - Try rating a module

2. **Check History**
   - Visit http://localhost:5000/history
   - After rating some modules, you should see them here

3. **Check API**
   ```bash
   # Get daily selection
   curl http://localhost:5000/api/daily
   
   # Health check
   curl http://localhost:5000/health
   ```

### Automated Testing (Coming Soon)

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

## Container Setup

### Using Podman (Single Container)

```bash
# Build image
podman build -t modplayer:latest .

# Run container
podman run -d \
  --name modplayer \
  -p 5000:5000 \
  -v modplayer-data:/app/data:Z \
  modplayer:latest

# View logs
podman logs -f modplayer

# Access at http://localhost:5000
```

### Using Docker Compose (With PostgreSQL)

```bash
# Create .env file with secure passwords
cat > .env << EOF
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Access at http://localhost:5000
```

### Using Kubernetes

See [k8s/README.md](k8s/README.md) for detailed instructions.

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Option 1: Change port in .env
echo "PORT=8000" >> .env

# Option 2: Set environment variable
export PORT=8000
python app.py
```

### Database Locked (SQLite)

If you get "database is locked" errors, make sure only one instance is running:

```bash
# Check for running instances
ps aux | grep "python app.py"

# Kill if needed
pkill -f "python app.py"
```

### Module Archive Not Responding

If Mod Archive is slow or unresponsive:

1. Wait a moment and refresh - the site may be temporarily busy
2. The app caches selections, so subsequent loads will be faster
3. Check the logs for specific errors: `tail -f logs/modplayer.log`

### ImportError: No module named 'flask'

Make sure your virtual environment is activated:

```bash
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### Cannot Find chiptune2.js

The app will work without chiptune2.js, but modules won't play in-browser. Instead, clicking "Play" will download the file. To enable in-browser playback, follow the instructions in `static/lib/README.md`.

## Next Steps

1. **Customize Configuration**: Edit `config.py` or `.env` to adjust module selection criteria
2. **Add Styling**: Customize `static/css/style.css` to match your preferences
3. **Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment options
4. **Contribute**: Found a bug? Have an idea? Contributions welcome!

## Useful Commands

```bash
# View logs
tail -f logs/modplayer.log

# Clear cache
rm -rf cache/modules/*

# Reset database (WARNING: deletes all data!)
rm data/database.db
python init_db.py

# Check Python version
python --version

# List installed packages
pip list

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Getting Help

- Check the logs in `logs/modplayer.log`
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Open an issue on GitHub
- Visit [The Mod Archive](https://modarchive.org) for module-related questions

## Have Fun!

Enjoy discovering amazing tracker music from the demoscene! 🎵✨
