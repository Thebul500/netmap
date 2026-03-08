"""Click CLI for netmap -- scan networks, fingerprint services, export results."""

import asyncio
import json
import sys
from pathlib import Path

import click

from . import __version__
from .export import save_results, results_to_json
from .scanner import DEFAULT_PORTS, parse_ports, scan_host, scan_network


# Module-level storage for last scan results (simple file-based persistence)
RESULTS_FILE = Path.home() / ".netmap" / "last_scan.json"


def _save_last_scan(results: list[dict]) -> None:
    """Persist the most recent scan results to disk."""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps(results, default=str), encoding="utf-8")


def _load_last_scan() -> list[dict]:
    """Load the most recent scan results from disk."""
    if not RESULTS_FILE.exists():
        return []
    try:
        return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _format_table(results: list[dict]) -> str:
    """Format scan results as a readable table."""
    if not results:
        return "No hosts discovered."

    lines: list[str] = []
    lines.append("")
    lines.append(f"  Discovered {len(results)} host(s)")
    lines.append(f"  {'=' * 70}")

    for host in results:
        ip = host["ip_address"]
        hostname = host.get("hostname", ip)
        device_type = host.get("device_type", "unknown")
        status = host.get("status", "online")

        header = f"  {ip}"
        if hostname != ip:
            header += f"  ({hostname})"
        header += f"  [{device_type}] [{status}]"
        lines.append(header)

        services = host.get("services", [])
        if services:
            lines.append(f"    {'PORT':<8} {'SERVICE':<15} {'VERSION'}")
            lines.append(f"    {'-' * 50}")
            for svc in services:
                port_str = str(svc["port"])
                service = svc.get("service", "unknown")
                version = svc.get("version", "")
                if len(version) > 40:
                    version = version[:37] + "..."
                lines.append(f"    {port_str:<8} {service:<15} {version}")
        else:
            open_ports = host.get("open_ports", [])
            lines.append(f"    Open ports: {', '.join(str(p) for p in open_ports)}")

        lines.append("")

    return "\n".join(lines)


@click.group()
@click.version_option(version=__version__, prog_name="netmap")
def cli():
    """netmap -- Network scanner with service fingerprinting.

    Scan networks and hosts to discover open ports and identify running services.
    """
    pass


@cli.command()
@click.argument("target")
@click.option(
    "-p", "--ports",
    default=None,
    help="Ports to scan (e.g. '22,80,443' or '1-1024'). Default: common ports.",
)
@click.option(
    "-c", "--concurrency",
    default=50,
    type=int,
    help="Max concurrent connections (default: 50).",
)
@click.option(
    "--no-fingerprint",
    is_flag=True,
    default=False,
    help="Skip service fingerprinting (faster).",
)
@click.option(
    "-o", "--output",
    default=None,
    help="Save results to file (.json or .csv).",
)
@click.option(
    "--json-output",
    "json_out",
    is_flag=True,
    default=False,
    help="Print results as JSON instead of a table.",
)
def scan(target: str, ports: str | None, concurrency: int, no_fingerprint: bool,
         output: str | None, json_out: bool):
    """Scan a host or network for open ports and services.

    TARGET can be a single IP (e.g. 10.0.2.1), a hostname, or a CIDR range
    (e.g. 10.0.2.0/24).

    Examples:

      netmap scan 10.0.2.1

      netmap scan 192.168.1.0/24 -p 22,80,443

      netmap scan 10.0.0.0/24 --no-fingerprint -o results.json
    """
    port_list = parse_ports(ports) if ports else DEFAULT_PORTS
    fingerprint = not no_fingerprint

    click.echo(f"Scanning {target} ({len(port_list)} ports)...")

    if "/" in target:
        # Network scan
        results = asyncio.run(
            scan_network(target, port_list, concurrency=concurrency, fingerprint=fingerprint)
        )
    else:
        # Single host scan
        result = asyncio.run(
            scan_host(target, port_list, fingerprint=fingerprint)
        )
        results = [result] if result else []

    # Save as last scan for later export
    _save_last_scan(results)

    # Output
    if json_out:
        click.echo(results_to_json(results))
    else:
        click.echo(_format_table(results))

    # Save to file if requested
    if output:
        saved_path = save_results(results, output)
        click.echo(f"Results saved to {saved_path}")

    if not results:
        sys.exit(0)


@cli.command()
@click.argument("output_path")
def export(output_path: str):
    """Export the last scan results to a file.

    Supported formats: .json, .csv

    Examples:

      netmap export results.json

      netmap export scan_data.csv
    """
    results = _load_last_scan()
    if not results:
        click.echo("No scan results found. Run 'netmap scan' first.", err=True)
        sys.exit(1)

    try:
        saved_path = save_results(results, output_path)
        click.echo(f"Exported {len(results)} host(s) to {saved_path}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the netmap CLI."""
    cli()


if __name__ == "__main__":
    main()
