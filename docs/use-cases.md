# Netmap Use Cases

## 1. Home Lab Network Inventory

Track every device on your home network. Register devices as you discover them and keep their status up to date.

```bash
# Register and log in
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@lab.local","password":"s3cret!"}'

TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@lab.local","password":"s3cret!"}' \
  | jq -r .access_token)

# Add your router
curl -s -X POST http://localhost:8000/devices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"opnsense","ip_address":"10.0.2.1","mac_address":"00:1a:2b:3c:4d:5e","device_type":"firewall"}'

# Add a server
curl -s -X POST http://localhost:8000/devices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"nas-01","ip_address":"10.0.2.50","mac_address":"aa:bb:cc:dd:ee:ff","device_type":"server"}'

# List all devices
curl -s http://localhost:8000/devices/ \
  -H "Authorization: Bearer $TOKEN" | jq .
```

This gives you a single API-driven source of truth for every host on your LAN.

## 2. Multi-Tenant Device Management

Netmap's per-user ownership model means multiple teams or users can share a single instance. Each user only sees devices they own, providing natural tenant isolation without complex RBAC.

**Team A** registers their development servers:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"team-a","email":"a@corp.dev","password":"teamA-pass"}'
```

**Team B** registers production infrastructure:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"team-b","email":"b@corp.dev","password":"teamB-pass"}'
```

Each team's `GET /devices/` call returns only their own devices.

## 3. Infrastructure Monitoring Integration

Use the health and readiness endpoints to integrate netmap with Kubernetes or other orchestrators:

```yaml
# Kubernetes liveness/readiness probes
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 3
  periodSeconds: 5
```

Poll `/health` from your monitoring system (Prometheus blackbox exporter, Uptime Kuma, etc.) to track API availability and version.

## 4. Automated Asset Tracking with Scripts

Combine netmap with network scanning tools to automatically populate your device inventory:

```python
import subprocess, json, requests

API = "http://localhost:8000"
TOKEN = "<your-jwt-token>"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Scan local subnet with nmap (requires nmap installed)
result = subprocess.run(
    ["nmap", "-sn", "10.0.2.0/24", "-oX", "-"],
    capture_output=True, text=True
)

# Parse discovered hosts and register them
# (simplified — real implementation would parse nmap XML)
for host in discovered_hosts:
    requests.post(f"{API}/devices/", headers=HEADERS, json={
        "hostname": host["hostname"],
        "ip_address": host["ip"],
        "mac_address": host.get("mac"),
        "device_type": "unknown",
        "status": "online",
    })
```

## 5. Device Lifecycle Management

Track device status changes over time. Mark devices offline when decommissioned, update hostnames after migrations:

```bash
# Mark a device as offline
curl -X PUT http://localhost:8000/devices/3 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"offline"}'

# Update hostname after migration
curl -X PUT http://localhost:8000/devices/3 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"db-primary-new","ip_address":"10.0.3.10"}'

# Decommission — remove device entirely
curl -X DELETE http://localhost:8000/devices/3 \
  -H "Authorization: Bearer $TOKEN"
```
