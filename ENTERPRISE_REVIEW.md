# Enterprise Readiness Review

Self-evaluation of netmap against the competitive landscape. Conducted 2026-03-06.

---

## Competitors

### 1. Nmap / Zenmap

- **GitHub stars**: ~12,200 ([nmap/nmap](https://github.com/nmap/nmap))
- **Language**: C / Lua (Zenmap: Python)
- **License**: NPSL (custom, GPL-like)
- **Target audience**: Security professionals, network administrators, penetration testers
- **Key features**: Host discovery, port scanning (SYN/TCP/UDP/SCTP), service/version detection, OS fingerprinting, NSE scripting engine (600+ scripts), Zenmap GUI with basic topology view, XML/grepable output formats
- **What we lack**: Service version detection, OS fingerprinting, UDP scanning, scripting engine, raw packet scanning (SYN scan), mature protocol support

### 2. NetBox

- **GitHub stars**: ~19,900 ([netbox-community/netbox](https://github.com/netbox-community/netbox))
- **Language**: Python (Django)
- **License**: Apache 2.0
- **Target audience**: Network engineers, data center operators, infrastructure teams
- **Key features**: IPAM (IP address management), DCIM (data center infrastructure management), circuit tracking, VLAN management, rack diagrams, extensive REST API, plugin ecosystem, webhook support, change logging, multi-tenancy, RBAC
- **What we lack**: IPAM, DCIM, VLAN tracking, rack/site modeling, plugin system, change logging, RBAC (we only have owner-based isolation)

### 3. IVRE

- **GitHub stars**: ~3,900 ([ivre/ivre](https://github.com/ivre/ivre))
- **Language**: Python
- **License**: GPL-3.0
- **Target audience**: Security researchers, red teams, threat intelligence analysts
- **Key features**: Network recon framework integrating Nmap/Masscan/Zeek/ZGrab2, passive DNS, flow analysis, MongoDB backend, web interface for browsing results, Python API + CLI, self-hosted Shodan/Censys alternative
- **What we lack**: Integration with external scanners, passive reconnaissance, flow analysis, advanced data warehouse capabilities

### 4. Angry IP Scanner

- **GitHub stars**: ~4,800 ([angryip/ipscan](https://github.com/angryip/ipscan))
- **Language**: Java
- **License**: GPL-2.0
- **Target audience**: IT generalists, home users, quick network audits
- **Key features**: Fast cross-platform ping sweep, port scanning, hostname resolution, MAC detection, CSV/TXT/XML export, plugin system for fetchers (NetBIOS, web detect)
- **What we lack**: Cross-platform desktop GUI, plugin system for fetchers

### 5. Masscan

- **GitHub stars**: ~25,300 ([robertdavidgraham/masscan](https://github.com/robertdavidgraham/masscan))
- **Language**: C
- **License**: AGPL-3.0
- **Target audience**: Security researchers doing internet-scale scanning
- **Key features**: Asynchronous TCP SYN scanning, custom TCP/IP stack, scans entire internet in <5 minutes, supports massive IP ranges
- **What we lack**: Raw packet scanning, custom TCP/IP stack, extreme-scale throughput (our scanner uses asyncio TCP connect, not raw SYN)

### 6. RustScan

- **GitHub stars**: ~15,500+ ([bee-san/RustScan](https://github.com/bee-san/RustScan))
- **Language**: Rust
- **License**: GPL-3.0
- **Target audience**: Penetration testers who want speed + Nmap integration
- **Key features**: Scans all 65,535 ports in 3 seconds, pipes results to Nmap, scripting engine (Python/Lua/Shell), adaptive learning
- **What we lack**: All-port scanning speed, Nmap piping, adaptive scan tuning

### 7. Netdisco

- **GitHub stars**: ~676 ([netdisco/netdisco](https://github.com/netdisco/netdisco))
- **Language**: Perl
- **License**: BSD
- **Target audience**: Enterprise network administrators with managed switches
- **Key features**: SNMP-based device/port inventory, MAC/IP/DNS search, VLAN tracking, network map visualization, 20+ years of maturity
- **What we lack**: SNMP polling, LLDP/CDP neighbor discovery, switch port mapping, VLAN awareness

### 8. OpenWISP Network Topology

- **GitHub stars**: ~195 ([openwisp/openwisp-network-topology](https://github.com/openwisp/openwisp-network-topology))
- **Language**: Python (Django)
- **License**: BSD-3-Clause
- **Target audience**: Wireless mesh network operators
- **Key features**: Topology collection from routing protocols (OLSR, batman-adv), OpenVPN topology, snapshot history, link status webhooks, REST API
- **What we lack**: Routing protocol integration, topology snapshot diffing, link-level monitoring

---

## Functionality Gaps

### What competitors have that we don't

| Feature | Nmap | NetBox | IVRE | netmap |
|---------|------|--------|------|--------|
| Active host discovery | Yes | No (IPAM only) | Yes (via Nmap) | Yes (TCP connect) |
| Port scanning | Yes (SYN/TCP/UDP) | No | Yes (via backends) | Yes (TCP connect only) |
| Service version detection | Yes | No | Yes | **No** |
| OS fingerprinting | Yes | No | Yes | **No** |
| Interactive topology map | Zenmap (basic) | No | Web UI (basic) | **No** |
| Static HTML export | No | No | No | **No** |
| JSON export | XML only | Yes | Yes | **No** (planned) |
| REST API | No | Yes (excellent) | Yes | Yes |
| Scan scheduling | No | N/A | Via cron | **No** |
| Change detection / diffing | No | Change log | No | **No** |
| IPAM | No | Yes | No | **No** |
| Multi-user with RBAC | No | Yes | Basic | Owner isolation only |
| Plugin/extension system | NSE scripts | Yes | No | **No** |
| Pagination | N/A | Yes | Yes | Yes (just added) |
| Input validation (IP/CIDR) | Yes | Yes | Yes | Yes (just added) |

### Core functions we're missing

1. **No service fingerprinting** -- We can detect open ports but cannot identify what service is running (e.g., "nginx 1.25" vs just "port 80 open"). Every serious competitor does this.

2. **No topology visualization** -- The project description promises "a live interactive map" but no visualization exists. No HTML export. No graph API endpoint. This is the headline feature and it's absent.

3. **No scan scheduling** -- Users cannot schedule recurring scans. There's no way to "scan my network every hour and alert me on changes." This is table stakes for monitoring tools.

4. **No change detection** -- No way to compare scan results over time. "What changed since last scan?" is the most requested feature in network monitoring forums.

5. **No UDP scanning** -- We only do TCP connect scans. DNS (53/udp), SNMP (161/udp), NTP (123/udp) are invisible to us.

### Common workflows we don't support

- "Show me everything on 192.168.1.0/24 as a visual map" -- can't do it (no visualization)
- "Alert me when a new device appears" -- can't do it (no change detection, no webhooks)
- "Export this scan as a report I can share" -- can't do it (no export)
- "Run this scan every day at midnight" -- can't do it (no scheduling)

### Edge cases unhandled

- Scanning large subnets (/16 = 65,534 hosts) may exhaust memory or time out with no progress feedback
- No rate limiting on scan creation -- a user could queue thousands of scans
- No scan cancellation -- once started, a scan runs to completion or failure
- IPv6 networks are accepted by CIDR validation but scanning behavior is untested

---

## Quality Gaps

### Code quality: Good

- Clean project structure: src layout, proper package, clear module separation
- Async throughout: FastAPI + SQLAlchemy async + asyncpg -- no sync anti-patterns
- Good test coverage: 52 tests covering auth, CRUD, cross-user isolation, validation, pagination, scans
- CI pipeline: lint (ruff), type check (mypy), security scan (bandit), tests with coverage
- Docker setup works: multi-stage build, docker-compose with health checks
- Security basics: bcrypt password hashing, JWT auth, no secrets in code, SECURITY.md

### Error messages: Adequate

- Validation errors return 422 with Pydantic detail explaining what's wrong
- Auth errors return 401 with clear messages ("Invalid credentials", "Invalid or expired token")
- 404s return "Device not found" / "Scan not found"
- No generic 500 error handler -- unhandled exceptions return raw FastAPI error (leaks stack trace in debug mode)

### Output quality: Needs work

- API responses are clean JSON via Pydantic serialization
- No request ID or correlation tracking for debugging
- No structured logging -- just default uvicorn stdout
- OpenAPI docs auto-generated but not enriched with descriptions or examples

### CLI: Non-existent

- The project entry point (`netmap = "netmap.app:create_app"`) doesn't work as a CLI scanner
- No `netmap scan 192.168.1.0/24` command-line experience
- Users must interact via HTTP API only -- high friction for quick scans

### Rough edges

- CORS is `allow_origins=["*"]` -- fine for dev, dangerous for production
- `docker-compose.yml` uses deprecated `version: "3.9"` key
- `pyproject.toml` entry point maps to `create_app` which returns a FastAPI instance, not a CLI entry
- The lifespan handler silently swallows all startup errors (`except Exception: pass`)
- No database migration for the new Scan model (relies on `create_all` which won't alter existing tables)

### Would a developer trust this in their daily workflow?

**Not yet.** The foundation is solid (FastAPI, async, proper auth, good tests), but the feature gap is too wide. A developer who needs network topology mapping would hit the wall immediately: there's no visualization, no export, no service detection. They'd switch to Nmap + a script within minutes.

---

## Improvement Plan

### Implemented in this review (3 improvements)

1. **IP/MAC address validation** -- `DeviceCreate` and `DeviceUpdate` now validate IP addresses (IPv4/IPv6) and MAC addresses using stdlib `ipaddress` and regex. CIDR validation added for `ScanCreate`. Previously accepted any string, which could cause data integrity issues. (`src/netmap/schemas.py`)

2. **Pagination on device list** -- `GET /devices/` now returns a paginated response with `items`, `total`, `page`, `page_size`, and `pages` fields. Supports `page` and `page_size` query params (default 50, max 200) and optional `status` filter. Previously returned an unbounded list that would degrade with large datasets. (`src/netmap/routes/devices.py`, `src/netmap/schemas.py`)

3. **Scan model and routes with async TCP scanner** -- Added complete scan lifecycle:
   - `Scan` model with status tracking (pending/running/completed/failed), timestamps, error messages
   - `POST /scans/` creates a scan and launches async background scanning via `BackgroundTasks`
   - `GET /scans/` lists scans, `GET /scans/{id}` returns scan detail with discovered devices
   - `DELETE /scans/{id}` removes a scan and its devices (cascade delete)
   - Async TCP connect scanner with configurable port list, concurrent host scanning (semaphore-bounded), reverse DNS, and heuristic device type guessing
   - CIDR validation on scan creation
   - (`src/netmap/scanner.py`, `src/netmap/routes/scans.py`, `src/netmap/models.py`)

### Remaining improvements needed (priority order)

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| P0 | **Topology visualization** -- Add `GET /topology/{scan_id}` returning a D3.js-compatible graph (nodes + edges), and `GET /export/{scan_id}/html` serving a self-contained HTML page with an interactive network map. This is the headline feature. | High | Critical |
| P0 | **JSON/CSV export** -- `GET /export/{scan_id}/json` returning structured scan results. Trivial to implement on top of existing data. | Low | High |
| P1 | **Service banner grabbing** -- After detecting an open port, read the service banner (first few bytes). Distinguishes "nginx" from "Apache" from "OpenSSH". | Medium | High |
| P1 | **Scan diffing** -- `GET /scans/{id}/diff?against={prev_id}` comparing two scans: new hosts, removed hosts, changed ports. Core differentiator from ANALYSIS.md. | Medium | High |
| P2 | **CLI interface** -- `netmap scan 192.168.1.0/24` command that starts the API, runs a scan, and prints results to stdout. Dramatically lowers friction. | Medium | High |
| P2 | **Structured logging** -- Replace print/default with structured JSON logging. Add request IDs. Essential for production debugging. | Low | Medium |
| P2 | **Scan scheduling** -- Cron-like recurring scans with `schedule` field on scan creation. | Medium | Medium |
| P3 | **Rate limiting** -- Limit auth endpoints and scan creation to prevent abuse. | Low | Medium |
| P3 | **Webhook notifications** -- POST to a URL when a scan completes or new devices are found. | Low | Medium |
| P3 | **Custom error handler** -- Return consistent JSON error responses for 500s, add request correlation IDs. | Low | Low |

---

## Final Verdict

**NOT READY** for real users.

### Reasoning

The project has a solid technical foundation:
- Well-structured FastAPI application with proper async patterns
- Working JWT authentication with bcrypt password hashing
- Comprehensive test suite (52 tests, all passing)
- CI/CD pipeline with lint, type check, security scan, and coverage
- Docker deployment that works out of the box
- Proper input validation (IP, MAC, CIDR) and paginated responses

However, the core value proposition -- "scans subnets, fingerprints services, builds a live interactive map" -- is only partially delivered:
- **Subnet scanning**: Now exists (TCP connect scan added in this review), but limited to TCP connect only. No UDP, no SYN scan, no service version detection.
- **Service fingerprinting**: Not implemented. Open ports are detected but not identified.
- **Interactive map**: Not implemented. No topology visualization, no HTML export, no graph API.

What we have is a device inventory API with basic scanning. What users expect based on the description is a network topology mapper with visualization. The gap between promise and delivery is too wide.

**To reach "READY" status**, the project needs at minimum:
1. Topology visualization (interactive HTML map of discovered devices)
2. JSON export of scan results
3. Service banner grabbing on open ports
4. A CLI interface for frictionless quick scans

These four additions would make netmap a viable lightweight alternative to the competitor set. Without them, users will evaluate the tool, find the missing features within 5 minutes, and move on.
