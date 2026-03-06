# Deployment Guide

## Docker Compose (Recommended)

The quickest way to run netmap in production.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2

### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Thebul500/netmap.git
   cd netmap
   ```

2. **Set a secure secret key:**

   ```bash
   export SECRET_KEY=$(openssl rand -hex 32)
   ```

3. **Start the stack:**

   ```bash
   docker compose up -d
   ```

   This starts two containers:
   - `app` — the netmap FastAPI server on port 8000
   - `postgres` — PostgreSQL 16 database on port 5432

4. **Verify the deployment:**

   ```bash
   curl http://localhost:8000/health
   # {"status":"healthy","version":"0.1.0","timestamp":"..."}
   ```

### Configuration

All settings are configured via environment variables with the `NETMAP_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `NETMAP_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/netmap` | Async database connection string |
| `NETMAP_SECRET_KEY` | `change-me-in-production` | Secret key for signing JWT tokens. **Must be changed in production.** |
| `NETMAP_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token lifetime in minutes |
| `NETMAP_DEBUG` | `false` | Enable debug mode (do not use in production) |

### Production Checklist

- [ ] Set `NETMAP_SECRET_KEY` to a random 32+ character string
- [ ] Change the default PostgreSQL password in `docker-compose.yml`
- [ ] Place a reverse proxy (nginx, Caddy, Traefik) in front of the app for TLS
- [ ] Set `NETMAP_DEBUG=false`
- [ ] Restrict the `postgres` port binding to localhost or remove it

## Manual Installation

For development or environments without Docker.

### Prerequisites

- Python 3.11+
- PostgreSQL 14+

### Steps

1. **Install dependencies:**

   ```bash
   pip install -e .
   ```

2. **Create the database:**

   ```bash
   createdb netmap
   ```

3. **Configure environment:**

   ```bash
   export NETMAP_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/netmap"
   export NETMAP_SECRET_KEY=$(openssl rand -hex 32)
   ```

4. **Run database migrations:**

   ```bash
   alembic upgrade head
   ```

5. **Start the server:**

   ```bash
   uvicorn netmap.app:app --host 0.0.0.0 --port 8000
   ```

## API Reference Summary

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Authenticate and receive a JWT token |

### Devices (requires JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/devices/` | Register a new device |
| GET | `/devices/` | List all devices owned by the current user |
| GET | `/devices/{id}` | Get a single device by ID |
| PUT | `/devices/{id}` | Update device fields |
| DELETE | `/devices/{id}` | Remove a device |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (returns status, version, timestamp) |
| GET | `/ready` | Readiness probe for orchestrators |

All authenticated endpoints require the header `Authorization: Bearer <token>`.
