# netmap — Project Plan

Network topology auto-discovery tool. Scans subnets, fingerprints services, builds a live interactive map of all devices and open ports. Exports to JSON/HTML.

## Architecture

### System Overview

netmap is a FastAPI-based web service backed by PostgreSQL. Users authenticate via JWT, then create and manage **scans** against target subnets. A background scanner performs async host discovery and port scanning, storing results as **devices** and **ports**. A topology API serves the discovered network graph for visualization, and an export layer renders the data to JSON or static HTML.

```
┌─────────────┐       ┌──────────────────────────────────────┐
│   Client /   │       │            netmap API                │
│   Browser    │◄─────►│                                      │
└─────────────┘  HTTP  │  ┌──────────┐  ┌────────────────┐   │
                       │  │  Auth    │  │  Scan Engine   │   │
                       │  │  (JWT)   │  │  (async tasks) │   │
                       │  └──────────┘  └───────┬────────┘   │
                       │  ┌──────────┐          │             │
                       │  │  Export  │          ▼             │
                       │  │  (JSON/  │  ┌────────────────┐   │
                       │  │   HTML)  │  │  PostgreSQL    │   │
                       │  └──────────┘  └────────────────┘   │
                       └──────────────────────────────────────┘
```

### API Endpoints

#### Auth (`/auth`)

| Method | Path              | Description                  |
|--------|-------------------|------------------------------|
| POST   | `/auth/register`  | Create a new user account    |
| POST   | `/auth/login`     | Authenticate, return JWT     |
| GET    | `/auth/me`        | Get current user profile     |

#### Scans (`/scans`)

| Method | Path                     | Description                          |
|--------|--------------------------|--------------------------------------|
| POST   | `/scans`                 | Create a new scan (target CIDR)      |
| GET    | `/scans`                 | List all scans for current user      |
| GET    | `/scans/{id}`            | Get scan details and status          |
| DELETE | `/scans/{id}`            | Delete a scan and its results        |

#### Devices (`/devices`)

| Method | Path                     | Description                          |
|--------|--------------------------|--------------------------------------|
| GET    | `/devices`               | List discovered devices (filterable) |
| GET    | `/devices/{id}`          | Get device details with open ports   |

#### Topology (`/topology`)

| Method | Path                     | Description                          |
|--------|--------------------------|--------------------------------------|
| GET    | `/topology/{scan_id}`    | Get network graph for a scan         |

#### Export (`/export`)

| Method | Path                          | Description                     |
|--------|-------------------------------|---------------------------------|
| GET    | `/export/{scan_id}/json`      | Export scan results as JSON     |
| GET    | `/export/{scan_id}/html`      | Export interactive HTML map     |

#### Health (existing)

| Method | Path       | Description              |
|--------|------------|--------------------------|
| GET    | `/health`  | Application health check |
| GET    | `/ready`   | Readiness probe          |

### Data Model

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│  User    │       │    Scan      │       │  Device  │
├──────────┤       ├──────────────┤       ├──────────┤
│ id (PK)  │──1:N──│ id (PK)      │──1:N──│ id (PK)  │
│ username │       │ user_id (FK) │       │ scan_id  │
│ email    │       │ target_cidr  │       │ ip_addr  │
│ hashed_pw│       │ status       │       │ hostname │
│ created  │       │ started_at   │       │ mac_addr │
│ updated  │       │ finished_at  │       │ os_guess │
└──────────┘       │ created_at   │       │ is_up    │
                   │ updated_at   │       │ created  │
                   └──────────────┘       │ updated  │
                                          └────┬─────┘
                                               │
                                            1:N│
                                               ▼
                                          ┌──────────┐
                                          │   Port   │
                                          ├──────────┤
                                          │ id (PK)  │
                                          │ device_id│
                                          │ port_num │
                                          │ protocol │
                                          │ state    │
                                          │ service  │
                                          │ banner   │
                                          │ created  │
                                          │ updated  │
                                          └──────────┘
```

**Entities:**

- **User** — accounts with hashed passwords. Owns scans.
- **Scan** — a scan job targeting a CIDR range. Status: `pending`, `running`, `completed`, `failed`.
- **Device** — a discovered host on the network. Linked to one scan.
- **Port** — an open port on a device with service fingerprint and banner.

### Auth Flow

1. User registers with username, email, and password.
2. Password is hashed with bcrypt via `passlib`.
3. User logs in with credentials; server returns a signed JWT (HS256 via `python-jose`).
4. JWT contains `sub` (user ID) and `exp` (expiry, default 30 min, configurable via `NETMAP_ACCESS_TOKEN_EXPIRE_MINUTES`).
5. Protected endpoints require `Authorization: Bearer <token>` header.
6. A `get_current_user` dependency decodes the token, loads the user from the database, and injects it into the route.

### Deployment Architecture

**Development:** `docker compose up` runs the FastAPI app + PostgreSQL. Alembic manages schema migrations.

**Production:**
- Docker image built from the existing `Dockerfile`.
- PostgreSQL 16 in a managed instance or Docker volume.
- Uvicorn workers behind a reverse proxy (nginx or Traefik).
- Environment variables for all secrets (`NETMAP_SECRET_KEY`, `NETMAP_DATABASE_URL`).
- Health checks at `/health` and `/ready` for container orchestration.
- CI via GitHub Actions (lint, test, build).

## Technology

| Technology        | Role                  | Why                                                                                                  |
|-------------------|-----------------------|------------------------------------------------------------------------------------------------------|
| **Python 3.11+** | Language              | Async-first, rich networking libraries, large ecosystem for security/scanning tools.                 |
| **FastAPI**       | Web framework         | Native async support, automatic OpenAPI docs, Pydantic validation, dependency injection. Fast.       |
| **SQLAlchemy 2**  | ORM / data access     | Async engine via `asyncpg`, mature migration story with Alembic, declarative models.                 |
| **PostgreSQL 16** | Database              | JSONB for flexible scan metadata, robust indexing for IP/CIDR queries, ACID compliance.              |
| **asyncpg**       | DB driver             | Fastest async PostgreSQL driver for Python. Native prepared statements.                              |
| **Alembic**       | Migrations            | Tightly integrated with SQLAlchemy. Supports autogenerate and downgrade.                             |
| **JWT (python-jose)** | Authentication   | Stateless tokens — no session store needed. Standard, widely supported. HS256 for simplicity.        |
| **passlib/bcrypt**| Password hashing      | Industry-standard adaptive hashing. Resistant to brute-force attacks.                                |
| **Pydantic**      | Validation / schemas  | Enforces request/response contracts. Auto-generates OpenAPI schemas. Excellent error messages.        |
| **httpx**         | HTTP client           | Async HTTP client for integration tests and potential external API calls.                            |
| **Docker**        | Containerization      | Reproducible builds. Single `docker compose up` for full stack.                                      |
| **Ruff**          | Linting / formatting  | Extremely fast Python linter. Replaces flake8, isort, and black in one tool.                         |
| **pytest**        | Testing               | Async test support via `pytest-asyncio`. Coverage via `pytest-cov`.                                  |

## Milestones

### M1: Core Auth & Data Model

**Goal:** Users can register, log in, and the database schema is in place.

- [ ] Define `User`, `Scan`, `Device`, `Port` SQLAlchemy models
- [ ] Generate Alembic migration for initial schema
- [ ] Implement `/auth/register`, `/auth/login`, `/auth/me` endpoints
- [ ] JWT token creation and validation utilities
- [ ] `get_current_user` dependency for protected routes
- [ ] Pydantic schemas for all auth request/response types
- [ ] Unit tests for auth flow (register, login, protected access, invalid token)

### M2: Scan Management API

**Goal:** Users can create, list, and delete scan jobs.

- [ ] Implement `/scans` CRUD endpoints (POST, GET list, GET detail, DELETE)
- [ ] Scan status lifecycle (`pending` -> `running` -> `completed` / `failed`)
- [ ] Scoped access: users can only see their own scans
- [ ] Input validation for CIDR targets
- [ ] Pydantic schemas for scan request/response
- [ ] Integration tests for scan endpoints

### M3: Scan Engine

**Goal:** Scans actually discover hosts and ports.

- [ ] Async host discovery (ICMP ping sweep or TCP connect to common ports)
- [ ] Port scanning (configurable port list, TCP connect scan)
- [ ] Service fingerprinting (banner grab on open ports)
- [ ] OS guess heuristic (TTL-based or service-based)
- [ ] Background task execution (scan runs without blocking the API)
- [ ] Results persisted as `Device` and `Port` records
- [ ] Scan status updated on completion/failure
- [ ] Unit tests for scanner components

### M4: Topology & Device API

**Goal:** Discovered devices and network topology are queryable.

- [ ] Implement `/devices` list with filtering (by scan, IP range, service)
- [ ] Implement `/devices/{id}` detail with nested ports
- [ ] Implement `/topology/{scan_id}` returning a graph structure (nodes + edges)
- [ ] Pagination for device lists
- [ ] Tests for device and topology endpoints

### M5: Export

**Goal:** Scan results can be exported as JSON and interactive HTML.

- [ ] `/export/{scan_id}/json` — structured JSON dump of devices, ports, and metadata
- [ ] `/export/{scan_id}/html` — self-contained HTML page with a network visualization (D3.js or vis.js embedded)
- [ ] Access control: only scan owner can export
- [ ] Tests for export endpoints

### M6: Hardening & Production Readiness

**Goal:** The application is secure, documented, and ready for deployment.

- [ ] Rate limiting on auth endpoints
- [ ] Input sanitization and CIDR validation hardening
- [ ] CORS configuration for production
- [ ] Security policy (`SECURITY.md`)
- [ ] Contributing guide (`CONTRIBUTING.md`)
- [ ] API documentation in `docs/`
- [ ] CI pipeline: lint, test, coverage >= 80%, container build
- [ ] Performance benchmarks (`BENCHMARKS.md`)
- [ ] SBOM generation
- [ ] Container vulnerability scanning
- [ ] Competitive analysis (`ANALYSIS.md`)
