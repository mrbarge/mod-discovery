# ModPlayer Container Deployment Guide

This guide covers deploying ModPlayer using various container technologies: Podman, Docker, Docker Compose, and Kubernetes.

## Table of Contents

- [Quick Start Options](#quick-start-options)
- [Deployment Option 1: Podman (Single Container)](#deployment-option-1-podman-single-container)
- [Deployment Option 2: Docker (Single Container)](#deployment-option-2-docker-single-container)
- [Deployment Option 3: Docker Compose (Multi-Container)](#deployment-option-3-docker-compose-multi-container)
- [Deployment Option 4: Kubernetes](#deployment-option-4-kubernetes)
- [Configuration](#configuration)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

## Quick Start Options

### Simple Local Development
```bash
podman build -t modplayer:latest .
podman run -p 5000:5000 -v modplayer-data:/app/data modplayer:latest
```

### Production-like Environment
```bash
docker-compose up -d
```

### Production Kubernetes
```bash
kubectl apply -f k8s/
```

## Deployment Option 1: Podman (Single Container)

Podman is ideal for rootless, daemonless container deployment. This option uses SQLite in a single container.

### Prerequisites

- Podman 4.0+
- 512MB RAM minimum
- 2GB disk space for database and cache

### Build the Image

```bash
# Build the image
podman build -t modplayer:latest .

# Verify the build
podman images | grep modplayer
```

### Run the Container

#### Basic Run

```bash
podman run -d \
  --name modplayer \
  -p 5000:5000 \
  -v modplayer-data:/app/data:Z \
  modplayer:latest
```

#### Run with Custom Configuration

```bash
podman run -d \
  --name modplayer \
  -p 5000:5000 \
  -e DAILY_MODULE_COUNT_MIN=4 \
  -e DAILY_MODULE_COUNT_MAX=6 \
  -e CACHE_MAX_AGE_DAYS=60 \
  -v modplayer-data:/app/data:Z \
  -v modplayer-cache:/app/cache:Z \
  modplayer:latest
```

#### Rootless Podman

```bash
# Run as non-root user (recommended)
podman run -d \
  --name modplayer \
  --userns=keep-id \
  -p 5000:5000 \
  -v ~/.local/share/modplayer/data:/app/data:Z \
  modplayer:latest
```

### Generate Systemd Service

For automatic startup:

```bash
# Generate systemd unit file
podman generate systemd --new --name modplayer > ~/.config/systemd/user/modplayer.service

# Enable and start service
systemctl --user enable --now modplayer.service

# View status
systemctl --user status modplayer
```

### Manage the Container

```bash
# View logs
podman logs -f modplayer

# Stop container
podman stop modplayer

# Start container
podman start modplayer

# Restart container
podman restart modplayer

# Remove container
podman rm -f modplayer

# Remove image
podman rmi modplayer:latest
```

## Deployment Option 2: Docker (Single Container)

Similar to Podman but using Docker.

### Prerequisites

- Docker 20.10+
- Docker daemon running

### Build and Run

```bash
# Build
docker build -t modplayer:latest .

# Run
docker run -d \
  --name modplayer \
  -p 5000:5000 \
  -v modplayer-data:/app/data \
  modplayer:latest

# View logs
docker logs -f modplayer

# Access at http://localhost:5000
```

### Docker with Restart Policy

```bash
docker run -d \
  --name modplayer \
  --restart unless-stopped \
  -p 5000:5000 \
  -v modplayer-data:/app/data \
  -v modplayer-cache:/app/cache \
  modplayer:latest
```

## Deployment Option 3: Docker Compose (Multi-Container)

Recommended for production-like environments with PostgreSQL.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Configuration

1. **Create Environment File**

Create `.env` file in project root:

```bash
# Database
DB_PASSWORD=your-secure-password-here

# Application
SECRET_KEY=your-secret-key-here
DAILY_MODULE_COUNT_MIN=3
DAILY_MODULE_COUNT_MAX=5
CACHE_MAX_AGE_DAYS=30
```

2. **Generate Secure Keys**

```bash
# Generate database password
openssl rand -base64 32

# Generate Flask secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Deploy

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f postgres

# Check status
docker-compose ps
```

### Manage Services

```bash
# Stop services
docker-compose stop

# Start services
docker-compose start

# Restart services
docker-compose restart

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (WARNING: deletes data!)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build
```

### Scale the Application

```bash
# Run multiple app instances (requires load balancer)
docker-compose up -d --scale app=3
```

### Access Services

- **Application**: http://localhost:5000
- **PostgreSQL**: localhost:5432 (from host)
  - Username: modplayer
  - Password: (from .env file)
  - Database: modplayer

### Database Operations

```bash
# Backup database
docker-compose exec postgres pg_dump -U modplayer modplayer > backup.sql

# Restore database
docker-compose exec -T postgres psql -U modplayer modplayer < backup.sql

# Access PostgreSQL shell
docker-compose exec postgres psql -U modplayer modplayer

# View database logs
docker-compose logs postgres
```

## Deployment Option 4: Kubernetes

See [k8s/README.md](k8s/README.md) for comprehensive Kubernetes deployment guide.

### Quick Kubernetes Deploy

```bash
# Deploy everything
kubectl apply -f k8s/

# Check status
kubectl get all -n modplayer

# Port forward for testing
kubectl port-forward -n modplayer service/modplayer 5000:5000
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | sqlite:///data/database.db | Database connection string |
| `SECRET_KEY` | (required) | Flask secret key |
| `FLASK_ENV` | production | Flask environment |
| `DAILY_MODULE_COUNT_MIN` | 3 | Minimum daily modules |
| `DAILY_MODULE_COUNT_MAX` | 5 | Maximum daily modules |
| `CACHE_DIR` | /app/cache/modules | Module cache directory |
| `CACHE_MAX_AGE_DAYS` | 30 | Cache retention days |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 5000 | Server port |

### Volume Mounts

#### Single Container (SQLite)

| Mount Point | Purpose | Recommended Size |
|-------------|---------|------------------|
| `/app/data` | Database file | 1GB |
| `/app/cache` | Module cache | 10GB+ |
| `/app/logs` | Application logs | 1GB |

#### Multi-Container (PostgreSQL)

**App Container:**
| Mount Point | Purpose | Recommended Size |
|-------------|---------|------------------|
| `/app/cache` | Module cache | 10GB+ |
| `/app/logs` | Application logs | 1GB |

**Database Container:**
| Mount Point | Purpose | Recommended Size |
|-------------|---------|------------------|
| `/var/lib/postgresql/data` | PostgreSQL data | 10GB+ |

## Maintenance

### Viewing Logs

**Podman:**
```bash
podman logs -f modplayer
podman logs --since 1h modplayer  # Last hour
podman logs --tail 100 modplayer  # Last 100 lines
```

**Docker:**
```bash
docker logs -f modplayer
```

**Docker Compose:**
```bash
docker-compose logs -f
docker-compose logs -f app  # Specific service
```

**Kubernetes:**
```bash
kubectl logs -n modplayer -l component=app -f
```

### Updating the Application

**Podman/Docker:**
```bash
# Stop container
podman stop modplayer

# Remove old container
podman rm modplayer

# Rebuild image
podman build -t modplayer:latest .

# Start new container
podman run -d --name modplayer -p 5000:5000 -v modplayer-data:/app/data modplayer:latest
```

**Docker Compose:**
```bash
# Rebuild and restart
docker-compose up -d --build
```

**Kubernetes:**
```bash
# Update image
kubectl set image deployment/modplayer modplayer=modplayer:v1.1.0 -n modplayer

# Or apply updated manifests
kubectl apply -f k8s/
```

### Backup and Restore

#### SQLite Database (Single Container)

**Backup:**
```bash
# Copy database file from volume
podman cp modplayer:/app/data/database.db ./backup-$(date +%Y%m%d).db

# Or use volume mount
podman run --rm -v modplayer-data:/data -v $(pwd):/backup alpine \
  cp /data/database.db /backup/database-backup.db
```

**Restore:**
```bash
# Stop container
podman stop modplayer

# Copy backup to volume
podman run --rm -v modplayer-data:/data -v $(pwd):/backup alpine \
  cp /backup/database-backup.db /data/database.db

# Start container
podman start modplayer
```

#### PostgreSQL Database (Multi-Container)

**Backup:**
```bash
docker-compose exec postgres pg_dump -U modplayer modplayer > backup-$(date +%Y%m%d).sql
```

**Restore:**
```bash
docker-compose exec -T postgres psql -U modplayer modplayer < backup.sql
```

### Clearing Cache

**Remove old cached modules:**

```bash
# Podman
podman exec modplayer python -c "from services.player import clear_old_cache; clear_old_cache(30)"

# Docker Compose
docker-compose exec app python -c "from services.player import clear_old_cache; clear_old_cache(30)"

# Or manually clean volume
podman run --rm -v modplayer-cache:/cache alpine sh -c "find /cache -mtime +30 -delete"
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
podman logs modplayer
docker logs modplayer
docker-compose logs app
```

**Common issues:**
- Port 5000 already in use → Change port mapping
- Database initialization failed → Check DATABASE_URL
- Permission issues → Check volume permissions (add `:Z` flag for SELinux)

### Database Connection Issues

**Verify database is running:**
```bash
# Docker Compose
docker-compose ps postgres

# Check database logs
docker-compose logs postgres
```

**Test connection:**
```bash
# From app container
docker-compose exec app python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"
```

### Can't Access Application

**Check if container is running:**
```bash
podman ps
docker ps
docker-compose ps
```

**Check port binding:**
```bash
podman port modplayer
```

**Test from host:**
```bash
curl http://localhost:5000/health
```

**Check firewall:**
```bash
# Open port in firewall
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

### Performance Issues

**Check resource usage:**
```bash
# Podman
podman stats modplayer

# Docker
docker stats modplayer

# Docker Compose
docker-compose ps
docker stats $(docker-compose ps -q)
```

**Increase resources:**
```bash
# Add resource limits
podman run -d \
  --name modplayer \
  --memory=1g \
  --cpus=2 \
  -p 5000:5000 \
  -v modplayer-data:/app/data \
  modplayer:latest
```

### Volume Issues

**List volumes:**
```bash
podman volume ls
docker volume ls
```

**Inspect volume:**
```bash
podman volume inspect modplayer-data
```

**Remove volumes:**
```bash
# WARNING: This deletes all data!
podman volume rm modplayer-data
docker volume rm modplayer-data
```

## Health Checks

### Manual Health Check

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-05T10:30:00Z"
}
```

### Container Health Status

```bash
# Podman
podman healthcheck run modplayer

# Docker
docker inspect --format='{{.State.Health.Status}}' modplayer
```

## Security Considerations

### 1. Use Secrets Properly

- Never commit secrets to Git
- Use environment files (.env) and add to .gitignore
- Rotate secrets regularly

### 2. Run as Non-Root

**Podman (already rootless):**
```bash
podman run --userns=keep-id ...
```

**Docker:**
Add to Dockerfile:
```dockerfile
USER nobody
```

### 3. Network Isolation

**Docker Compose** (already configured):
- App and database on private network
- Only expose app port externally

### 4. Volume Permissions

Use SELinux labels for volumes:
```bash
podman run -v modplayer-data:/app/data:Z ...
```

### 5. Scan Images for Vulnerabilities

```bash
# Podman
podman scan modplayer:latest

# Docker
docker scan modplayer:latest
```

## Production Checklist

- [ ] Change default passwords and secret keys
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Set up automated backups
- [ ] Configure monitoring and alerting
- [ ] Implement log rotation
- [ ] Set resource limits
- [ ] Test disaster recovery procedures
- [ ] Document runbooks
- [ ] Set up CI/CD pipeline

## Additional Resources

- [Podman Documentation](https://docs.podman.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Flask Deployment](https://flask.palletsprojects.com/en/latest/deploying/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
