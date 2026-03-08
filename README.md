# netmap

Network topology auto-discovery tool. Scans subnets, fingerprints services, builds a live interactive map of all devices and open ports. Exports to JSON/HTML.

[![CI](https://github.com/Thebul500/netmap/actions/workflows/ci.yml/badge.svg)](https://github.com/Thebul500/netmap/actions)

## Quick Start

```bash
docker compose up -d
curl http://localhost:8000/health
```

## Installation (Development)

```bash
pip install -e .[dev]
uvicorn netmap.app:app --reload
```

## Usage

```bash
# Start with Docker Compose (recommended)
docker compose up -d

# Or run directly
uvicorn netmap.app:app --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |

## Configuration

Environment variables (prefix `NETMAP_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Database connection string |
| `SECRET_KEY` | *(auto-generated)* | JWT signing key |
| `DEBUG` | `false` | Enable debug mode |
