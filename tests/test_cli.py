"""Tests for the Click CLI."""

import json
import os
import tempfile
from unittest import mock

from click.testing import CliRunner

from netmap.cli import cli, _format_table, _save_last_scan, _load_last_scan


# ── Table formatting ─────────────────────────────────────────


class TestFormatTable:
    def test_empty_results(self):
        output = _format_table([])
        assert "No hosts" in output

    def test_single_host_with_services(self):
        results = [{
            "ip_address": "10.0.2.1",
            "hostname": "gateway.local",
            "open_ports": [22, 80],
            "services": [
                {"port": 22, "service": "ssh", "version": "OpenSSH_8.9", "banner": ""},
                {"port": 80, "service": "http", "version": "nginx/1.24", "banner": ""},
            ],
            "status": "online",
            "device_type": "server",
        }]
        output = _format_table(results)
        assert "10.0.2.1" in output
        assert "gateway.local" in output
        assert "ssh" in output
        assert "http" in output
        assert "server" in output
        assert "1 host" in output

    def test_multiple_hosts(self):
        results = [
            {
                "ip_address": "10.0.2.1",
                "hostname": "10.0.2.1",
                "open_ports": [22],
                "services": [{"port": 22, "service": "ssh", "version": "", "banner": ""}],
                "status": "online",
                "device_type": "server",
            },
            {
                "ip_address": "10.0.2.2",
                "hostname": "10.0.2.2",
                "open_ports": [80],
                "services": [{"port": 80, "service": "http", "version": "", "banner": ""}],
                "status": "online",
                "device_type": "web_server",
            },
        ]
        output = _format_table(results)
        assert "2 host" in output
        assert "10.0.2.1" in output
        assert "10.0.2.2" in output

    def test_host_without_services_key(self):
        """Hosts without 'services' key should show open_ports fallback."""
        results = [{
            "ip_address": "10.0.2.1",
            "hostname": "10.0.2.1",
            "open_ports": [22, 80],
            "status": "online",
            "device_type": "server",
        }]
        output = _format_table(results)
        assert "22" in output
        assert "80" in output


# ── Last scan persistence ────────────────────────────────────


class TestLastScanPersistence:
    def test_save_and_load(self, tmp_path):
        results = [{"ip_address": "10.0.0.1", "open_ports": [22]}]
        results_file = tmp_path / "last_scan.json"

        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            _save_last_scan(results)
            loaded = _load_last_scan()

        assert loaded == results

    def test_load_missing_file(self, tmp_path):
        results_file = tmp_path / "nonexistent.json"
        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            loaded = _load_last_scan()
        assert loaded == []


# ── CLI commands ─────────────────────────────────────────────


class TestScanCommand:
    def test_scan_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", "--help"])
        assert result.exit_code == 0
        assert "TARGET" in result.output
        assert "--ports" in result.output

    def test_scan_single_host_mocked(self, tmp_path):
        """Scan a single host with mocked scanner."""
        fake_result = {
            "ip_address": "10.0.2.1",
            "hostname": "gateway",
            "open_ports": [22, 80],
            "services": [
                {"port": 22, "service": "ssh", "version": "OpenSSH_8.9", "banner": ""},
                {"port": 80, "service": "http", "version": "nginx", "banner": ""},
            ],
            "status": "online",
            "device_type": "server",
        }

        async def mock_scan_host(ip, ports, fingerprint=True):
            return fake_result

        results_file = tmp_path / "last_scan.json"
        runner = CliRunner()
        with mock.patch("netmap.cli.scan_host", side_effect=mock_scan_host):
            with mock.patch("netmap.cli.RESULTS_FILE", results_file):
                result = runner.invoke(cli, ["scan", "10.0.2.1", "-p", "22,80"])

        assert result.exit_code == 0
        assert "10.0.2.1" in result.output
        assert "ssh" in result.output
        assert "http" in result.output

    def test_scan_network_mocked(self, tmp_path):
        """Scan a CIDR range with mocked scanner."""
        fake_results = [
            {
                "ip_address": "10.0.0.1",
                "hostname": "host1",
                "open_ports": [22],
                "services": [{"port": 22, "service": "ssh", "version": "", "banner": ""}],
                "status": "online",
                "device_type": "server",
            },
        ]

        async def mock_scan_network(cidr, ports, concurrency=50, fingerprint=True):
            return fake_results

        results_file = tmp_path / "last_scan.json"
        runner = CliRunner()
        with mock.patch("netmap.cli.scan_network", side_effect=mock_scan_network):
            with mock.patch("netmap.cli.RESULTS_FILE", results_file):
                result = runner.invoke(cli, ["scan", "10.0.0.0/30", "-p", "22"])

        assert result.exit_code == 0
        assert "10.0.0.1" in result.output
        assert "1 host" in result.output

    def test_scan_no_results(self, tmp_path):
        """Scan that finds nothing should still exit 0."""
        async def mock_scan_host(ip, ports, fingerprint=True):
            return None

        results_file = tmp_path / "last_scan.json"
        runner = CliRunner()
        with mock.patch("netmap.cli.scan_host", side_effect=mock_scan_host):
            with mock.patch("netmap.cli.RESULTS_FILE", results_file):
                result = runner.invoke(cli, ["scan", "10.0.0.1", "-p", "1"])

        assert result.exit_code == 0
        assert "No hosts" in result.output

    def test_scan_json_output(self, tmp_path):
        """--json-output should produce valid JSON."""
        fake_result = {
            "ip_address": "10.0.2.1",
            "hostname": "10.0.2.1",
            "open_ports": [22],
            "services": [{"port": 22, "service": "ssh", "version": "", "banner": ""}],
            "status": "online",
            "device_type": "server",
        }

        async def mock_scan_host(ip, ports, fingerprint=True):
            return fake_result

        results_file = tmp_path / "last_scan.json"
        runner = CliRunner()
        with mock.patch("netmap.cli.scan_host", side_effect=mock_scan_host):
            with mock.patch("netmap.cli.RESULTS_FILE", results_file):
                result = runner.invoke(cli, ["scan", "10.0.2.1", "-p", "22", "--json-output"])

        assert result.exit_code == 0
        # The output should contain valid JSON (skip the "Scanning..." line)
        lines = result.output.strip().split("\n")
        json_text = "\n".join(lines[1:])  # Skip "Scanning..." line
        data = json.loads(json_text)
        assert data["host_count"] == 1

    def test_scan_with_file_output(self, tmp_path):
        """--output should save results to a file."""
        fake_result = {
            "ip_address": "10.0.2.1",
            "hostname": "10.0.2.1",
            "open_ports": [22],
            "services": [{"port": 22, "service": "ssh", "version": "", "banner": ""}],
            "status": "online",
            "device_type": "server",
        }

        async def mock_scan_host(ip, ports, fingerprint=True):
            return fake_result

        output_file = str(tmp_path / "scan.json")
        results_file = tmp_path / "last_scan.json"
        runner = CliRunner()
        with mock.patch("netmap.cli.scan_host", side_effect=mock_scan_host):
            with mock.patch("netmap.cli.RESULTS_FILE", results_file):
                result = runner.invoke(cli, ["scan", "10.0.2.1", "-p", "22", "-o", output_file])

        assert result.exit_code == 0
        assert os.path.exists(output_file)
        data = json.loads(open(output_file).read())
        assert data["host_count"] == 1


class TestExportCommand:
    def test_export_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "OUTPUT_PATH" in result.output

    def test_export_no_previous_scan(self, tmp_path):
        results_file = tmp_path / "nonexistent.json"
        runner = CliRunner()
        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            result = runner.invoke(cli, ["export", str(tmp_path / "out.json")])
        assert result.exit_code == 1
        assert "No scan results" in result.output

    def test_export_json(self, tmp_path):
        results = [{"ip_address": "10.0.2.1", "hostname": "gw", "open_ports": [22],
                     "services": [{"port": 22, "service": "ssh", "version": "", "banner": ""}],
                     "device_type": "server"}]
        results_file = tmp_path / "last_scan.json"

        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            _save_last_scan(results)

        output_file = str(tmp_path / "export.json")
        runner = CliRunner()
        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            result = runner.invoke(cli, ["export", output_file])

        assert result.exit_code == 0
        assert "Exported 1 host" in result.output
        data = json.loads(open(output_file).read())
        assert data["host_count"] == 1

    def test_export_csv(self, tmp_path):
        results = [{"ip_address": "10.0.2.1", "hostname": "gw", "open_ports": [22, 80],
                     "services": [
                         {"port": 22, "service": "ssh", "version": "OpenSSH_8.9", "banner": ""},
                         {"port": 80, "service": "http", "version": "nginx", "banner": ""},
                     ],
                     "device_type": "server"}]
        results_file = tmp_path / "last_scan.json"

        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            _save_last_scan(results)

        output_file = str(tmp_path / "export.csv")
        runner = CliRunner()
        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            result = runner.invoke(cli, ["export", output_file])

        assert result.exit_code == 0
        csv_content = open(output_file).read()
        assert "ip_address" in csv_content  # header
        assert "10.0.2.1" in csv_content
        assert "ssh" in csv_content
        assert "http" in csv_content

    def test_export_unsupported_format(self, tmp_path):
        results = [{"ip_address": "10.0.2.1", "open_ports": [22]}]
        results_file = tmp_path / "last_scan.json"

        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            _save_last_scan(results)

        output_file = str(tmp_path / "export.xml")
        runner = CliRunner()
        with mock.patch("netmap.cli.RESULTS_FILE", results_file):
            result = runner.invoke(cli, ["export", output_file])

        assert result.exit_code == 1
        assert "Unsupported" in result.output


class TestVersionFlag:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.2.0" in result.output
