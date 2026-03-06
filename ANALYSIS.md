# Competitive Analysis — netmap

Research conducted: March 2026

## Existing Tools

### 1. Nmap / Zenmap

- **GitHub stars**: ~35,000+ (nmap.org, not primarily GitHub-hosted)
- **Language**: C / Lua (Zenmap: Python)
- **License**: NPSL (custom, GPL-like)

**Key features**: The gold standard for network scanning. Host discovery, port scanning, service/version detection, OS fingerprinting, NSE scripting engine. Zenmap provides a desktop GUI with basic topology visualization.

**What users complain about**:
- Zenmap is a desktop-only GTK app — no web interface, no REST API, no way to integrate programmatically without parsing XML output
- Zenmap's topology view is rudimentary and non-interactive by modern standards
- No built-in scheduling, continuous monitoring, or change detection
- Output formats (XML, grepable) require additional tooling to make useful
- Zenmap has been stagnant; Python 2 to 3 migration was slow and painful for users

**Verdict**: Nmap is unbeatable for raw scanning. But it's a CLI tool, not a topology platform. Getting from "nmap scan" to "shareable network map" requires gluing together multiple tools.

### 2. Scanopy

- **GitHub stars**: ~4,100
- **Language**: Go (server), TypeScript (frontend)
- **License**: AGPL-3.0

**Key features**: Self-hosted network scanner with auto-discovery, interactive topology visualization, 200+ service definitions, SNMP v2c polling, LLDP/CDP neighbor discovery, Docker container detection, distributed scanning via daemons, scheduled scans, topology versioning/branching, REST API with granular permissions, multi-user with RBAC.

**What users complain about**:
- Relatively new (launched late 2025), still maturing — some features feel incomplete
- AGPL-3.0 license is a dealbreaker for some commercial/embedded use cases
- Requires a full deployment stack (server + daemon + database)
- Unraid/TrueNAS community reports occasional discovery failures on complex networks
- No Python SDK or library — it's a standalone application, not embeddable

**Verdict**: Scanopy is the closest direct competitor and a strong one. It does almost exactly what netmap aims to do. Any honest analysis must acknowledge this tool covers the core use case well.

### 3. Netdisco

- **GitHub stars**: ~824
- **Language**: Perl
- **License**: BSD

**Key features**: Web-based network management tool. Collects IP/MAC/wireless data via SNMP and SSH into PostgreSQL. Device inventory, port mapping, network map visualization, search by MAC/IP/DNS, supports VLAN tracking. Mature project (20+ years).

**What users complain about**:
- Written in Perl — hard to contribute to or extend for most developers
- SNMP-centric: limited usefulness on networks without managed switches
- Discovery depends on SNMP being enabled and properly configured on devices
- Web UI feels dated; no modern SPA frontend
- No REST API (or very limited); not designed for automation
- Installation is notoriously difficult (Perl dependencies, CPAN issues)

**Verdict**: Netdisco is excellent for enterprise switch/router inventory where SNMP is universal. Poor fit for scanning home labs, cloud networks, or mixed environments where SNMP isn't available.

### 4. IVRE

- **GitHub stars**: ~3,900
- **Language**: Python
- **License**: GPL-3.0

**Key features**: Network recon framework. Self-hosted alternative to Shodan/Censys/GreyNoise. Integrates Nmap, Masscan, ZGrab2, Zeek. MongoDB backend. Web interface for browsing scan results, passive DNS, network flow analysis. Python API and CLI.

**What users complain about**:
- Steep learning curve; documentation assumes significant security expertise
- MongoDB dependency adds operational complexity
- More focused on security recon than network management/topology
- No interactive topology visualization — it's a data warehouse, not a mapper
- Setup requires multiple components (web server, database, scanning agents)

**Verdict**: IVRE is powerful for security teams doing large-scale recon. Not designed for the "scan my network and show me a map" use case. Different target audience.

### 5. Angry IP Scanner

- **GitHub stars**: ~4,800
- **Language**: Java
- **License**: GPL-2.0

**Key features**: Fast, cross-platform IP/port scanner with GUI. Ping sweep, port scan, hostname resolution, MAC address detection. Export to CSV/TXT/XML. Plugin system for fetchers (NetBIOS, web server detection).

**What users complain about**:
- Desktop-only Java app — no web interface, no API, no headless mode
- No topology visualization whatsoever; it's a flat list/table
- No service fingerprinting beyond basic port detection
- Flagged as PUA by some antivirus (Bitdefender)
- Single developer project with slow issue resolution
- No scheduling, no continuous monitoring, no change tracking

**Verdict**: Good for quick one-off IP sweeps. Not a network mapping or topology tool. More of a lightweight nmap alternative for simple tasks.

### 6. Masscan

- **GitHub stars**: ~25,300
- **Language**: C
- **License**: AGPL-3.0

**Key features**: Ultra-fast asynchronous TCP port scanner. Can scan the entire internet in under 5 minutes. Custom TCP/IP stack for maximum performance. Supports massive IP ranges.

**What users complain about**:
- Sacrifices accuracy for speed — drops responses, misses services
- CLI only, zero visualization, zero topology
- Custom TCP/IP stack conflicts with the host OS stack
- No service fingerprinting (only detects open ports, not what's running)
- No web interface, no API, no export beyond raw lists
- Bugs in the latest release; users advised to build from source

**Verdict**: A raw speed tool for internet-scale scanning. Completely different use case from network topology mapping. Not a competitor — more of a potential scanning backend.

### 7. OpenWISP Network Topology

- **GitHub stars**: ~195
- **Language**: Python (Django)
- **License**: BSD-3-Clause

**Key features**: Django-based topology collector and visualizer. Designed for mesh/wireless networks. Collects topology from routing protocols (OLSR, batman-adv, etc.) and OpenVPN. Snapshot history, link status webhooks, REST API.

**What users complain about**:
- Narrow focus: built for wireless mesh networks, not general-purpose
- Does not perform active scanning — relies on external topology data sources
- Limited protocol support (only specific routing protocol formats)
- Part of the larger OpenWISP ecosystem; standalone use is awkward
- Small community, slow development pace

**Verdict**: Niche tool for mesh network operators. Not applicable to general subnet scanning and device discovery.

## Gap Analysis

### What existing tools do well

The space is not empty. Honest assessment:

- **Raw scanning** is solved: Nmap and Masscan handle host/port discovery thoroughly
- **Enterprise network management** is solved: Netdisco, NetBox (with plugins), and commercial tools (SolarWinds, Auvik, PRTG) cover managed networks
- **Self-hosted topology mapping** is increasingly solved: Scanopy in particular covers auto-discovery + interactive topology + REST API

### What no tool does well

| Gap | Details |
|-----|---------|
| **Lightweight, pip-installable Python tool** | Every existing tool requires Docker, system packages, or complex setup. No tool offers `pip install netmap && netmap scan 192.168.1.0/24` simplicity. Scanopy needs Go + Docker. IVRE needs MongoDB. Netdisco needs Perl + CPAN. |
| **API-first design for automation** | Most tools are UI-first with API bolted on afterward. No tool is designed primarily as a REST API that developers consume programmatically — for CI/CD pipelines, infrastructure-as-code validation, or automated inventory. |
| **Scan diffing / change detection** | Tools show current network state. Almost none highlight *what changed* since the last scan. "3 new hosts appeared, port 22 closed on server X, new service detected on Y" — this is what ops teams actually need for ongoing monitoring. |
| **Single-file static HTML export** | Most tools require a running server to view results. No tool produces a single portable HTML file (with embedded JS/CSS) that you can email to a colleague, attach to a ticket, or commit to a repo. JSON export is common but not human-friendly. |
| **Developer-oriented workflow** | Existing tools target network admins. Developers who want to understand their infrastructure programmatically (query devices in code, integrate with deployment scripts, run topology checks in CI) are underserved. |
| **Permissive licensing** | Scanopy (AGPL), Masscan (AGPL), Nmap (NPSL), IVRE (GPL) — the strongest open-source options all use copyleft licenses. MIT-licensed alternatives in this space are scarce. |

### What users repeatedly ask for (across GitHub issues and forums)

1. "How do I get a web-based network map without deploying a full NMS?"
2. "I just want to scan my subnet and get a visual topology — why is this so hard?"
3. "Can I run this in a Docker container and hit an API endpoint?"
4. "I need to detect when new devices join my network"
5. "I want to export the map as a standalone file I can share"

## Differentiator

### netmap's positioning

Given the competitive landscape, building "another Scanopy" would be redundant. Instead, netmap should position itself as:

**A developer-first network topology API** — lightweight, API-native, Python-based.

### Specific differentiators

1. **Zero-config quickstart**: `pip install netmap` or `docker run netmap`. Single command to scan and serve results. No multi-component deployment. PostgreSQL is optional (SQLite default for small networks).

2. **API-first architecture**: Every feature is an API endpoint first, UI second. Designed for consumption by scripts, CI/CD pipelines, and other tools. Clean JSON responses with proper pagination, filtering, and webhook support.

3. **Scan diffing**: First-class change detection. Every scan is compared against the previous one. API endpoint: `GET /api/scans/{id}/diff` returns added hosts, removed hosts, changed ports, new services. Webhook notifications on changes.

4. **Static HTML export**: `GET /api/topology/export?format=html` returns a single self-contained HTML file with an interactive D3.js topology map. No server needed to view it. Also: JSON, CSV, and Graphviz DOT export.

5. **MIT license**: Permissively licensed. Embeddable in commercial products, internal tools, or other open-source projects without copyleft concerns.

6. **Python ecosystem native**: Built with FastAPI, usable as a library (`from netmap import Scanner`), not just a standalone service. Familiar stack for the Python/DevOps community.

### What netmap is NOT trying to be

- Not an Nmap replacement — we use Nmap (or similar async scanning) under the hood
- Not an enterprise NMS — no SNMP polling, no switch configuration management
- Not a security recon platform — no passive DNS, no internet-scale scanning
- Not a full monitoring solution — no alerting dashboards, no uptime tracking

### Risk: Scanopy overlap

Scanopy is the biggest competitive risk. It's well-funded (commercial cloud tier), actively developed, and covers the core use case. Our differentiation depends on:
- Being genuinely simpler (pip install vs. Docker stack)
- Being API-first rather than UI-first
- Scan diffing as a first-class feature
- Permissive MIT license
- Python library usability (not just a service)

If Scanopy adds these features, our differentiation narrows. We should move fast on the API-first and diff features — they're architectural decisions that are hard to retrofit.
