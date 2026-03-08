"""Tests for the export module -- JSON and CSV serialization."""

import csv
import io
import json
import os

from netmap.export import results_to_csv, results_to_json, save_results


SAMPLE_RESULTS = [
    {
        "ip_address": "10.0.2.1",
        "hostname": "gateway.local",
        "open_ports": [22, 80],
        "services": [
            {"port": 22, "service": "ssh", "version": "OpenSSH_8.9", "banner": "SSH-2.0-OpenSSH_8.9"},
            {"port": 80, "service": "http", "version": "nginx/1.24", "banner": "HTTP/1.1 200 OK"},
        ],
        "status": "online",
        "device_type": "server",
    },
    {
        "ip_address": "10.0.2.2",
        "hostname": "pihole.local",
        "open_ports": [53, 80],
        "services": [
            {"port": 53, "service": "dns", "version": "", "banner": ""},
            {"port": 80, "service": "http", "version": "lighttpd", "banner": ""},
        ],
        "status": "online",
        "device_type": "dns_server",
    },
]


# ── JSON export ──────────────────────────────────────────────


class TestJsonExport:
    def test_valid_json(self):
        output = results_to_json(SAMPLE_RESULTS)
        data = json.loads(output)
        assert data["host_count"] == 2
        assert len(data["hosts"]) == 2
        assert "scan_time" in data

    def test_pretty_print(self):
        pretty = results_to_json(SAMPLE_RESULTS, pretty=True)
        compact = results_to_json(SAMPLE_RESULTS, pretty=False)
        assert len(pretty) > len(compact)
        assert "\n" in pretty

    def test_empty_results(self):
        output = results_to_json([])
        data = json.loads(output)
        assert data["host_count"] == 0
        assert data["hosts"] == []

    def test_host_data_preserved(self):
        output = results_to_json(SAMPLE_RESULTS)
        data = json.loads(output)
        host = data["hosts"][0]
        assert host["ip_address"] == "10.0.2.1"
        assert host["hostname"] == "gateway.local"
        assert host["services"][0]["service"] == "ssh"


# ── CSV export ───────────────────────────────────────────────


class TestCsvExport:
    def test_valid_csv(self):
        output = results_to_csv(SAMPLE_RESULTS)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Header + 4 service rows (2 hosts x 2 services each)
        assert len(rows) == 5
        assert rows[0] == ["ip_address", "hostname", "device_type", "port", "service", "version"]

    def test_csv_data(self):
        output = results_to_csv(SAMPLE_RESULTS)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # First data row
        assert rows[1][0] == "10.0.2.1"
        assert rows[1][1] == "gateway.local"
        assert rows[1][3] == "22"
        assert rows[1][4] == "ssh"

    def test_empty_results(self):
        output = results_to_csv([])
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        # Only header
        assert len(rows) == 1

    def test_host_without_services(self):
        """Hosts with open_ports but no services key should use fallback."""
        results = [{
            "ip_address": "10.0.2.1",
            "hostname": "10.0.2.1",
            "open_ports": [22, 80],
            "device_type": "server",
        }]
        output = results_to_csv(results)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) == 3  # header + 2 port rows


# ── save_results ─────────────────────────────────────────────


class TestSaveResults:
    def test_save_json(self, tmp_path):
        path = str(tmp_path / "output.json")
        result_path = save_results(SAMPLE_RESULTS, path)
        assert os.path.exists(result_path)
        data = json.loads(open(result_path).read())
        assert data["host_count"] == 2

    def test_save_csv(self, tmp_path):
        path = str(tmp_path / "output.csv")
        result_path = save_results(SAMPLE_RESULTS, path)
        assert os.path.exists(result_path)
        content = open(result_path).read()
        assert "ip_address" in content
        assert "10.0.2.1" in content

    def test_unsupported_format(self, tmp_path):
        path = str(tmp_path / "output.xml")
        try:
            save_results(SAMPLE_RESULTS, path)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported" in str(e)
