# PROSIM Deployment Guide

## Quick Start

### Docker (Recommended)

```bash
# Production
docker compose up -d

# Development (hot reload)
docker compose --profile dev up prosim-dev
```

The app will be available at `http://localhost:8000`.

### Local (No Docker)

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install with web dependencies
pip install -e ".[web]"

# Run
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

## Environment Variables

All configuration is via environment variables. Defaults are suitable for development.

| Variable | Default | Description |
|----------|---------|-------------|
| `PROSIM_SECRET_KEY` | `dev-secret-key-change-in-production` | Session signing key. **Set in production.** |
| `PROSIM_DATABASE_URL` | `sqlite:///./data/prosim.db` | SQLAlchemy database URL |
| `PROSIM_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` in Docker) |
| `PROSIM_PORT` | `8000` | Listen port |
| `PROSIM_DEBUG` | `false` | Enable debug mode (SQL logging, etc.) |

### Generating a Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Docker Details

### Production (`Dockerfile`)

Multi-stage build using `python:3.11-slim`:

1. **Build stage** -- installs package + web dependencies into `/install` prefix
2. **Runtime stage** -- copies installed packages and app source, runs as non-root `prosim` user

Features:
- Non-root user for security
- Health check on `/health` endpoint
- `PYTHONUNBUFFERED=1` for proper log streaming
- `PYTHONDONTWRITEBYTECODE=1` to avoid `.pyc` clutter

### Development (`Dockerfile.dev`)

Single-stage build with editable install (`pip install -e ".[web,dev]"`).
Source directories are bind-mounted for hot reload via `uvicorn --reload`.

### Data Persistence

SQLite database is stored at `/app/data/prosim.db` inside the container.
The `prosim_data` Docker volume is mounted at `/app/data` to persist data across container restarts.

```bash
# Back up the database
docker compose exec prosim cp /app/data/prosim.db /app/data/prosim.db.bak
docker compose cp prosim:/app/data/prosim.db.bak ./prosim-backup.db

# View volume location
docker volume inspect prosim_data
```

### Building and Running

```bash
# Build production image
docker compose build prosim

# Run in foreground (see logs)
docker compose up prosim

# Run in background
docker compose up -d prosim

# View logs
docker compose logs -f prosim

# Stop
docker compose down

# Stop and remove volumes (DELETES DATA)
docker compose down -v
```

### Custom Port or Secret Key

```bash
# Via environment variables
PROSIM_SECRET_KEY=my-secret-key PROSIM_PORT=3000 docker compose up -d

# Or via .env file (create in project root)
echo 'PROSIM_SECRET_KEY=my-secret-key' > .env
echo 'PROSIM_PORT=3000' >> .env
docker compose up -d
```

## Reverse Proxy

For production, place PROSIM behind a reverse proxy (nginx, Caddy, Traefik) for TLS termination.

### Caddy (simplest)

```
prosim.example.com {
    reverse_proxy localhost:8000
}
```

### Nginx

```nginx
server {
    listen 443 ssl;
    server_name prosim.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Architecture Notes

- **FastAPI** serves the web interface with Jinja2 templates
- **SQLite** stores game sessions and decision history as JSON blobs
- **No external services** required (no Redis, Postgres, etc.)
- **Single process** is sufficient -- SQLite handles concurrent reads well, and game state writes are infrequent
- The `/health` endpoint returns `{"status": "healthy"}` for monitoring
