# Real-World Validation Report

## Environment

| Parameter       | Value                                    |
|-----------------|------------------------------------------|
| Date            | 2026-03-06                               |
| Host OS         | Linux 6.17.0-14-generic (Ubuntu)         |
| Docker Engine   | Docker Compose v2                        |
| App Image       | `netmap-app` (python:3.12-alpine)        |
| Database        | postgres:16-alpine                       |
| Network         | Docker bridge (netmap_default)           |

## Stack Startup

**Timestamp:** 2026-03-06T10:05:32Z

```
$ docker compose up --build -d

 Container netmap-postgres-1  Created
 Container netmap-app-1       Created
 Container netmap-postgres-1  Healthy
 Container netmap-app-1       Started
```

Both containers started successfully. Postgres healthcheck passed before the app container was started (depends_on condition: service_healthy). App logs confirmed:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Tables were auto-created on startup via `Base.metadata.create_all` in the lifespan handler.

---

## Test Results

### 1. Health Check (`GET /health`)

**Timestamp:** 2026-03-06T10:06:48Z | **Status:** 200 OK

```json
{"status":"healthy","version":"0.1.0","timestamp":"2026-03-06T10:06:48.888616Z"}
```

### 2. Readiness Probe (`GET /ready`)

**Timestamp:** 2026-03-06T10:06:49Z | **Status:** 200 OK

```json
{"status":"ready"}
```

### 3. User Registration (`POST /auth/register`)

**Timestamp:** 2026-03-06T10:06:54Z | **Status:** 201 Created

```json
{"id":1,"username":"testuser","email":"test@netmap.dev","created_at":"2026-03-06T10:06:54.429436"}
```

### 4. User Login (`POST /auth/login`)

**Timestamp:** 2026-03-06T10:06:59Z | **Status:** 200 OK

```
Token: eyJhbGciOiJIUzI1NiIs...GPfn8uSDF9A7TNHtgDTY
```

JWT token returned with HS256 algorithm. Token used for all subsequent authenticated requests.

### 5. Duplicate Registration (negative test)

**Timestamp:** 2026-03-06T10:07:05Z | **Status:** 400 Bad Request

```json
{"detail":"Username or email already registered"}
```

### 6. Invalid Login (negative test)

**Timestamp:** 2026-03-06T10:07:05Z | **Status:** 401 Unauthorized

```json
{"detail":"Invalid credentials"}
```

### 7. Unauthenticated Access (negative test)

**Timestamp:** 2026-03-06T10:07:05Z | **Status:** 401 Unauthorized

```json
{"detail":"Not authenticated"}
```

### 8. Create Device 1 (`POST /devices/`)

**Timestamp:** 2026-03-06T10:07:14Z | **Status:** 201 Created

```json
{
  "id": 1,
  "hostname": "opnsense-fw",
  "ip_address": "10.0.2.1",
  "mac_address": "00:1a:2b:3c:4d:5e",
  "device_type": "firewall",
  "status": "online",
  "owner_id": 1,
  "created_at": "2026-03-06T10:07:14.568540",
  "updated_at": "2026-03-06T10:07:14.568540"
}
```

### 9. Create Device 2 (`POST /devices/`)

**Timestamp:** 2026-03-06T10:07:14Z | **Status:** 201 Created

```json
{
  "id": 2,
  "hostname": "pihole-dns",
  "ip_address": "10.0.2.2",
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "device_type": "dns_server",
  "status": "online",
  "owner_id": 1
}
```

### 10. Create Device 3 — nullable mac_address (`POST /devices/`)

**Timestamp:** 2026-03-06T10:07:14Z | **Status:** 201 Created

```json
{
  "id": 3,
  "hostname": "ollama-gpu",
  "ip_address": "10.0.3.144",
  "mac_address": null,
  "device_type": "compute",
  "status": "online",
  "owner_id": 1
}
```

### 11. List All Devices (`GET /devices/`)

**Timestamp:** 2026-03-06T10:07:23Z | **Status:** 200 OK

Returned array of 3 devices. All fields populated correctly including timestamps.

### 12. Get Single Device (`GET /devices/1`)

**Timestamp:** 2026-03-06T10:07:19Z | **Status:** 200 OK

```json
{
  "id": 1,
  "hostname": "opnsense-fw",
  "ip_address": "10.0.2.1",
  "mac_address": "00:1a:2b:3c:4d:5e",
  "device_type": "firewall",
  "status": "online",
  "owner_id": 1
}
```

### 13. Get Nonexistent Device (negative test)

**Timestamp:** 2026-03-06T10:07:19Z | **Status:** 404 Not Found

```json
{"detail":"Device not found"}
```

### 14. Update Device (`PUT /devices/3`)

**Timestamp:** 2026-03-06T10:07:32Z | **Status:** 200 OK

Partial update: added `mac_address` and changed `status` to "maintenance".

```json
{
  "id": 3,
  "hostname": "ollama-gpu",
  "ip_address": "10.0.3.144",
  "mac_address": "11:22:33:44:55:66",
  "device_type": "compute",
  "status": "maintenance",
  "owner_id": 1,
  "updated_at": "2026-03-06T10:07:32.014596"
}
```

`updated_at` timestamp changed from the original `created_at` value, confirming the `onupdate` trigger works.

### 15. Verify Update (`GET /devices/3`)

**Timestamp:** 2026-03-06T10:07:32Z | **Status:** 200 OK

Confirmed `mac_address` and `status` fields persisted correctly after update.

### 16. Delete Device (`DELETE /devices/2`)

**Timestamp:** 2026-03-06T10:07:32Z | **Status:** 204 No Content

Empty response body as expected.

### 17. Verify Deletion (`GET /devices/2`)

**Timestamp:** 2026-03-06T10:07:32Z | **Status:** 404 Not Found

```json
{"detail":"Device not found"}
```

### 18. List After Delete (`GET /devices/`)

**Timestamp:** 2026-03-06T10:07:32Z | **Status:** 200 OK

```
Device count: 2
  - opnsense-fw (10.0.2.1) [online]
  - ollama-gpu (10.0.3.144) [maintenance]
```

### 19. Cross-User Isolation

**Timestamp:** 2026-03-06T10:07:39Z

Registered `user2`, logged in, and verified:
- `GET /devices/` returns empty list (user2 owns no devices) — **200 OK**
- `GET /devices/1` returns 404 (device belongs to user1) — **404 Not Found**

Data isolation between users is enforced correctly via `owner_id` filtering.

### 20. OpenAPI Documentation

**Timestamp:** 2026-03-06T10:07:48Z | **Status:** 200 OK

- Swagger UI accessible at `/docs`
- OpenAPI JSON schema at `/openapi.json`
- 9 endpoints across 6 paths:

```
GET    /health
GET    /ready
POST   /auth/register
POST   /auth/login
GET    /devices/
POST   /devices/
GET    /devices/{device_id}
PUT    /devices/{device_id}
DELETE /devices/{device_id}
```

---

## Summary

| Category           | Tests | Passed | Failed |
|--------------------|-------|--------|--------|
| Health/Readiness   | 2     | 2      | 0      |
| Authentication     | 5     | 5      | 0      |
| Device CRUD        | 9     | 9      | 0      |
| Authorization      | 2     | 2      | 0      |
| OpenAPI Docs       | 2     | 2      | 0      |
| **Total**          | **20**| **20** | **0**  |

## Fix Applied

The app lifespan handler was empty — database tables were never created on startup. Added `Base.metadata.create_all` to the `lifespan()` function in `src/netmap/app.py` so tables are auto-created when the app boots. Without this fix, all database operations would fail with `relation "users" does not exist`.

## Limitations

- No rate limiting on auth endpoints (registration, login).
- No input validation on IP/MAC address format (accepts any string).
- No pagination on `GET /devices/` — will degrade with large datasets.
- `updated_at` uses database-level `onupdate` which requires SQLAlchemy to detect changes; direct SQL updates would bypass it.
- The `version` attribute in `docker-compose.yml` is obsolete (Docker Compose v2 warning).

## Teardown

**Timestamp:** 2026-03-06T10:07:52Z

```
$ docker compose down -v
 Container netmap-app-1       Removed
 Container netmap-postgres-1  Removed
 Volume netmap_pgdata         Removed
 Network netmap_default       Removed
```

Stack fully cleaned up. No persistent state remains.
