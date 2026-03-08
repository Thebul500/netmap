"""Async network scanner -- TCP connect scan, banner grabbing, service fingerprinting."""

import asyncio
import ipaddress
import re
import socket


# Well-known port-to-service mapping for fallback when banner grab fails
PORT_SERVICE_MAP: dict[int, str] = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    465: "smtps",
    587: "smtp",
    993: "imaps",
    995: "pop3s",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    6379: "redis",
    8080: "http-proxy",
    8443: "https-alt",
    9090: "prometheus",
    27017: "mongodb",
}

# Ports that send a banner immediately upon connection (server-speaks-first)
BANNER_PORTS: set[int] = {21, 22, 25, 110, 143, 3306, 6379}

# Ports where we need to send a probe to get a response
HTTP_PORTS: set[int] = {80, 443, 8080, 8443, 9090}

# Regex patterns for identifying services from banners
SERVICE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ssh", re.compile(r"^SSH-[\d.]+-(.*)", re.IGNORECASE)),
    ("smtp", re.compile(r"^220[ -].*SMTP", re.IGNORECASE)),
    ("smtp", re.compile(r"^220[ -].*mail", re.IGNORECASE)),
    ("smtp", re.compile(r"^220[ -].*Postfix", re.IGNORECASE)),
    ("ftp", re.compile(r"^220[ -].*ftp", re.IGNORECASE)),
    ("ftp", re.compile(r"^220[ -].*FileZilla", re.IGNORECASE)),
    ("ftp", re.compile(r"^220[ -].*vsftpd", re.IGNORECASE)),
    ("pop3", re.compile(r"^\+OK", re.IGNORECASE)),
    ("imap", re.compile(r"^\* OK.*IMAP", re.IGNORECASE)),
    ("mysql", re.compile(r".*mysql", re.IGNORECASE)),
    ("redis", re.compile(r"^-ERR|^\$|^\+PONG|^-DENIED", re.IGNORECASE)),
    ("postgresql", re.compile(r".*PostgreSQL", re.IGNORECASE)),
    ("http", re.compile(r"^HTTP/[\d.]+ \d{3}", re.IGNORECASE)),
    ("http", re.compile(r"Server:", re.IGNORECASE)),
    ("dns", re.compile(r".*dns", re.IGNORECASE)),
    ("mongodb", re.compile(r".*MongoDB", re.IGNORECASE)),
]


async def tcp_connect(ip: str, port: int, timeout: float = 1.5) -> bool:
    """Attempt a TCP connection to ip:port. Returns True if port is open."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
        return False


async def grab_banner(ip: str, port: int, timeout: float = 3.0) -> str:
    """Connect to ip:port and grab the service banner.

    For server-speaks-first protocols (SSH, FTP, SMTP, etc.), just reads.
    For HTTP ports, sends a minimal HEAD request.
    Returns the banner string, or empty string on failure.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout,
        )
    except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
        return ""

    try:
        if port in HTTP_PORTS:
            # Send a minimal HTTP request
            request = f"HEAD / HTTP/1.0\r\nHost: {ip}\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()

        # Read up to 1024 bytes
        data = await asyncio.wait_for(reader.read(1024), timeout=2.0)
        banner = data.decode("utf-8", errors="replace").strip()
        return banner
    except (asyncio.TimeoutError, OSError, UnicodeDecodeError):
        return ""
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except OSError:
            pass


def identify_service(port: int, banner: str) -> dict[str, str]:
    """Identify the service running on a port from its banner.

    Returns a dict with 'service' name and 'version' (if detected).
    """
    service = PORT_SERVICE_MAP.get(port, "unknown")
    version = ""

    if not banner:
        return {"service": service, "version": version}

    # Try pattern matching on the banner
    for svc_name, pattern in SERVICE_PATTERNS:
        match = pattern.search(banner)
        if match:
            service = svc_name
            # Extract version info from the banner if possible
            if match.groups():
                version = match.group(1).strip()
            break

    # Special version extraction for common services
    if not version:
        if service == "ssh" and banner.startswith("SSH-"):
            # SSH-2.0-OpenSSH_8.9p1
            parts = banner.split("-", 2)
            if len(parts) >= 3:
                version = parts[2].strip()
        elif service == "http":
            # Look for Server: header
            server_match = re.search(r"Server:\s*(.+)", banner, re.IGNORECASE)
            if server_match:
                version = server_match.group(1).strip()
        elif service == "ftp" and banner.startswith("220"):
            # 220 (vsFTPd 3.0.5)
            version = banner[4:].strip().strip("()")
        elif service == "smtp" and banner.startswith("220"):
            version = banner[4:].strip()

    return {"service": service, "version": version}


async def scan_port(ip: str, port: int, fingerprint: bool = True, timeout: float = 1.5) -> dict | None:
    """Scan a single port on a host. Returns port info dict if open, else None."""
    is_open = await tcp_connect(ip, port, timeout=timeout)
    if not is_open:
        return None

    result: dict = {"port": port}

    if fingerprint:
        banner = await grab_banner(ip, port, timeout=3.0)
        svc_info = identify_service(port, banner)
        result["service"] = svc_info["service"]
        result["version"] = svc_info["version"]
        result["banner"] = banner[:200] if banner else ""
    else:
        result["service"] = PORT_SERVICE_MAP.get(port, "unknown")
        result["version"] = ""
        result["banner"] = ""

    return result


async def reverse_dns(ip: str) -> str:
    """Attempt reverse DNS lookup. Returns hostname or the IP itself."""
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyaddr, ip),
            timeout=2.0,
        )
        return result[0]
    except (socket.herror, socket.gaierror, asyncio.TimeoutError, OSError):
        return ip


async def scan_host(
    ip: str,
    ports: list[int],
    fingerprint: bool = True,
) -> dict | None:
    """Scan a single host. Returns device dict if any port is open, else None."""
    tasks = [scan_port(ip, port, fingerprint=fingerprint) for port in ports]
    results = await asyncio.gather(*tasks)

    port_results = [r for r in results if r is not None]
    if not port_results:
        return None

    open_ports = [r["port"] for r in port_results]
    hostname = await reverse_dns(ip)

    services = []
    for r in port_results:
        services.append({
            "port": r["port"],
            "service": r["service"],
            "version": r["version"],
            "banner": r.get("banner", ""),
        })

    return {
        "ip_address": ip,
        "hostname": hostname,
        "open_ports": open_ports,
        "services": services,
        "status": "online",
        "device_type": _guess_device_type(open_ports),
    }


async def scan_network(
    cidr: str,
    ports: list[int],
    concurrency: int = 50,
    fingerprint: bool = True,
) -> list[dict]:
    """Scan all hosts in a CIDR range. Returns list of discovered devices."""
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = [str(ip) for ip in network.hosts()]

    if not hosts:
        return []

    results: list[dict] = []
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_scan(ip: str) -> dict | None:
        async with semaphore:
            return await scan_host(ip, ports, fingerprint=fingerprint)

    tasks = [bounded_scan(ip) for ip in hosts]
    scan_results = await asyncio.gather(*tasks)

    for result in scan_results:
        if result is not None:
            results.append(result)

    return results


# Default ports to scan when none are specified
DEFAULT_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587,
    993, 995, 3306, 3389, 5432, 6379, 8080, 8443, 9090, 27017,
]


def parse_ports(ports_str: str) -> list[int]:
    """Parse a comma-separated port string into a list of ints."""
    ports: list[int] = []
    for part in ports_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            ports.extend(range(int(start), int(end) + 1))
        else:
            ports.append(int(part))
    return sorted(set(ports))


def _guess_device_type(open_ports: list[int]) -> str:
    """Heuristic device type based on open ports."""
    port_set = set(open_ports)

    if 53 in port_set:
        return "dns_server"
    if 80 in port_set or 443 in port_set or 8080 in port_set:
        if 22 in port_set:
            return "server"
        return "web_server"
    if 22 in port_set:
        return "server"
    if 3306 in port_set or 5432 in port_set:
        return "database"
    if 161 in port_set:
        return "network_device"
    return "unknown"
