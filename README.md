# netmap

Network scanner with async TCP port detection, device discovery, and REST API. Scans subnets, identifies open ports, performs reverse DNS lookups, and stores results in PostgreSQL.

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
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and get JWT token |
| POST | `/scans/` | Create and start a new scan |
| GET | `/scans/` | List all scans for current user |
| GET | `/scans/{scan_id}` | Get scan details with discovered devices |
| DELETE | `/scans/{scan_id}` | Delete a scan |
| POST | `/devices/` | Create a device manually |
| GET | `/devices/` | List devices (paginated, filterable) |
| GET | `/devices/{device_id}` | Get a single device |
| PUT | `/devices/{device_id}` | Update a device |
| DELETE | `/devices/{device_id}` | Delete a device |

## Configuration

Environment variables (prefix `NETMAP_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Database connection string |
| `SECRET_KEY` | *(auto-generated)* | JWT signing key |
| `DEBUG` | `false` | Enable debug mode |
