"""Export scan results to JSON and CSV formats."""

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path


def results_to_json(results: list[dict], pretty: bool = True) -> str:
    """Serialize scan results to a JSON string."""
    export_data = {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "host_count": len(results),
        "hosts": results,
    }
    if pretty:
        return json.dumps(export_data, indent=2, default=str)
    return json.dumps(export_data, default=str)


def results_to_csv(results: list[dict]) -> str:
    """Serialize scan results to a CSV string.

    Each row is one service on one host:
        ip_address, hostname, device_type, port, service, version
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ip_address", "hostname", "device_type", "port", "service", "version"])

    for host in results:
        services = host.get("services", [])
        if services:
            for svc in services:
                writer.writerow([
                    host["ip_address"],
                    host.get("hostname", ""),
                    host.get("device_type", ""),
                    svc["port"],
                    svc["service"],
                    svc.get("version", ""),
                ])
        else:
            # Fallback for results without service fingerprinting
            for port in host.get("open_ports", []):
                writer.writerow([
                    host["ip_address"],
                    host.get("hostname", ""),
                    host.get("device_type", ""),
                    port,
                    "",
                    "",
                ])

    return output.getvalue()


def save_results(results: list[dict], output_path: str) -> str:
    """Save scan results to a file. Format is inferred from the file extension.

    Supported extensions: .json, .csv
    Returns the absolute path of the written file.
    """
    path = Path(output_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        content = results_to_csv(results)
    elif suffix == ".json":
        content = results_to_json(results)
    else:
        raise ValueError(f"Unsupported file format: {suffix!r}. Use .json or .csv")

    path.write_text(content, encoding="utf-8")
    return str(path.resolve())
