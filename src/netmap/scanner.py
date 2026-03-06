"""Async network scanner — TCP connect scan for host/port discovery."""

import asyncio
import ipaddress
import socket


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


async def scan_host(ip: str, ports: list[int]) -> dict | None:
    """Scan a single host. Returns device dict if any port is open, else None."""
    open_ports = []

    tasks = [tcp_connect(ip, port) for port in ports]
    results = await asyncio.gather(*tasks)

    for port, is_open in zip(ports, results):
        if is_open:
            open_ports.append(port)

    if not open_ports:
        return None

    hostname = await reverse_dns(ip)

    return {
        "ip_address": ip,
        "hostname": hostname,
        "open_ports": open_ports,
        "status": "online",
        "device_type": _guess_device_type(open_ports),
    }


async def scan_network(cidr: str, ports: list[int], concurrency: int = 50) -> list[dict]:
    """Scan all hosts in a CIDR range. Returns list of discovered devices."""
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = [str(ip) for ip in network.hosts()]

    if not hosts:
        return []

    results: list[dict] = []
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_scan(ip: str) -> dict | None:
        async with semaphore:
            return await scan_host(ip, ports)

    tasks = [bounded_scan(ip) for ip in hosts]
    scan_results = await asyncio.gather(*tasks)

    for result in scan_results:
        if result is not None:
            results.append(result)

    return results


def parse_ports(ports_str: str) -> list[int]:
    """Parse a comma-separated port string into a list of ints."""
    ports = []
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
