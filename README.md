# netmap

Network scanner with service fingerprinting. Scans subnets, identifies services via banner grabbing, and exports results to JSON/CSV.

[![CI](https://github.com/Thebul500/netmap/actions/workflows/ci.yml/badge.svg)](https://github.com/Thebul500/netmap/actions)

## Features

- **TCP port scanning** -- async connect scanning with configurable concurrency
- **Service fingerprinting** -- banner grabbing to identify SSH, HTTP, FTP, SMTP, MySQL, PostgreSQL, Redis, DNS, and more
- **Reverse DNS** -- automatic hostname resolution for discovered hosts
- **Device type detection** -- heuristic classification (server, web_server, database, dns_server, etc.)
- **JSON/CSV export** -- save scan results for analysis or reporting
- **Clean CLI** -- readable table output with optional JSON mode

## Installation

```bash
pip install -e .
```

## Usage

### Scan a single host

```bash
netmap scan 10.0.2.1
netmap scan 10.0.2.1 -p 22,80,443,8080
```

### Scan a subnet

```bash
netmap scan 192.168.1.0/24
netmap scan 10.0.2.0/24 -p 22,80,443 -c 100
```

### Skip fingerprinting (faster)

```bash
netmap scan 10.0.0.0/24 --no-fingerprint
```

### Output as JSON

```bash
netmap scan 10.0.2.1 --json-output
```

### Save results directly

```bash
netmap scan 10.0.2.0/24 -o results.json
netmap scan 10.0.2.0/24 -o results.csv
```

### Export last scan results

```bash
netmap export results.json
netmap export results.csv
```

## Example Output

```
  Discovered 3 host(s)
  ======================================================================
  10.0.2.1  (gateway.local)  [server] [online]
    PORT     SERVICE         VERSION
    --------------------------------------------------
    22       ssh             OpenSSH_8.9p1
    80       http            nginx/1.24.0
    443      https

  10.0.2.2  (pihole.local)  [dns_server] [online]
    PORT     SERVICE         VERSION
    --------------------------------------------------
    53       dns
    80       http            lighttpd/1.4.69

  10.0.2.10  [server] [online]
    PORT     SERVICE         VERSION
    --------------------------------------------------
    22       ssh             OpenSSH_9.6p1
```

## Development

```bash
pip install -e .[dev]
pytest -v
```

## License

MIT
