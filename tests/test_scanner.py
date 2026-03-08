"""Tests for the network scanner -- TCP scanning, banner grabbing, service identification."""

import asyncio
from unittest import mock

import pytest

from netmap.scanner import (
    DEFAULT_PORTS,
    grab_banner,
    identify_service,
    parse_ports,
    reverse_dns,
    scan_host,
    scan_network,
    scan_port,
    tcp_connect,
    _guess_device_type,
)


# ── parse_ports ────────────────────────────────────────────────


class TestParsePorts:
    def test_single_port(self):
        assert parse_ports("80") == [80]

    def test_multiple_ports(self):
        assert parse_ports("22,80,443") == [22, 80, 443]

    def test_port_range(self):
        assert parse_ports("20-22") == [20, 21, 22]

    def test_mixed(self):
        result = parse_ports("22,80-82,443")
        assert result == [22, 80, 81, 82, 443]

    def test_deduplicates(self):
        assert parse_ports("80,80,80") == [80]

    def test_sorts(self):
        assert parse_ports("443,22,80") == [22, 80, 443]

    def test_whitespace(self):
        assert parse_ports(" 22 , 80 , 443 ") == [22, 80, 443]


# ── _guess_device_type ────────────────────────────────────────


class TestGuessDeviceType:
    def test_dns_server(self):
        assert _guess_device_type([53, 80]) == "dns_server"

    def test_web_server(self):
        assert _guess_device_type([80, 443]) == "web_server"

    def test_server_with_ssh_and_web(self):
        assert _guess_device_type([22, 80]) == "server"

    def test_ssh_only(self):
        assert _guess_device_type([22]) == "server"

    def test_database(self):
        assert _guess_device_type([3306]) == "database"
        assert _guess_device_type([5432]) == "database"

    def test_network_device(self):
        assert _guess_device_type([161]) == "network_device"

    def test_unknown(self):
        assert _guess_device_type([12345]) == "unknown"


# ── identify_service ─────────────────────────────────────────


class TestIdentifyService:
    def test_ssh_banner(self):
        result = identify_service(22, "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6")
        assert result["service"] == "ssh"
        assert "OpenSSH" in result["version"]

    def test_http_banner(self):
        banner = "HTTP/1.1 200 OK\r\nServer: nginx/1.24.0\r\n"
        result = identify_service(80, banner)
        assert result["service"] == "http"
        assert "nginx" in result["version"]

    def test_ftp_banner(self):
        result = identify_service(21, "220 (vsFTPd 3.0.5)")
        assert result["service"] == "ftp"

    def test_smtp_banner(self):
        result = identify_service(25, "220 mail.example.com ESMTP Postfix")
        assert result["service"] == "smtp"

    def test_redis_banner(self):
        result = identify_service(6379, "-ERR wrong number of arguments")
        assert result["service"] == "redis"

    def test_pop3_banner(self):
        result = identify_service(110, "+OK Dovecot ready.")
        assert result["service"] == "pop3"

    def test_imap_banner(self):
        result = identify_service(143, "* OK [CAPABILITY IMAP4rev1] Dovecot ready.")
        assert result["service"] == "imap"

    def test_no_banner_falls_back_to_port_map(self):
        result = identify_service(3306, "")
        assert result["service"] == "mysql"
        assert result["version"] == ""

    def test_unknown_port_no_banner(self):
        result = identify_service(9999, "")
        assert result["service"] == "unknown"

    def test_unknown_port_with_banner(self):
        result = identify_service(9999, "SSH-2.0-dropbear_2022.83")
        assert result["service"] == "ssh"


# ── tcp_connect (localhost) ───────────────────────────────────


class TestTcpConnect:
    @pytest.mark.asyncio
    async def test_connect_to_closed_port(self):
        """Port 1 is almost certainly closed on localhost."""
        result = await tcp_connect("127.0.0.1", 1, timeout=0.5)
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        """Non-routable IP should time out."""
        result = await tcp_connect("192.0.2.1", 80, timeout=0.3)
        assert result is False


# ── grab_banner ──────────────────────────────────────────────


class TestGrabBanner:
    @pytest.mark.asyncio
    async def test_banner_closed_port(self):
        """Banner grab on a closed port returns empty string."""
        result = await grab_banner("127.0.0.1", 1, timeout=0.5)
        assert result == ""

    @pytest.mark.asyncio
    async def test_banner_unreachable(self):
        """Banner grab on unreachable host returns empty string."""
        result = await grab_banner("192.0.2.1", 80, timeout=0.3)
        assert result == ""


# ── scan_port ────────────────────────────────────────────────


class TestScanPort:
    @pytest.mark.asyncio
    async def test_closed_port_returns_none(self):
        result = await scan_port("127.0.0.1", 1, fingerprint=True, timeout=0.5)
        assert result is None

    @pytest.mark.asyncio
    async def test_scan_port_no_fingerprint(self):
        """With fingerprint=False, should still return port map service if open."""
        # Mock tcp_connect to return True
        with mock.patch("netmap.scanner.tcp_connect", return_value=True):
            result = await scan_port("127.0.0.1", 22, fingerprint=False, timeout=0.5)
            assert result is not None
            assert result["port"] == 22
            assert result["service"] == "ssh"
            assert result["version"] == ""


# ── scan_host ────────────────────────────────────────────────


class TestScanHost:
    @pytest.mark.asyncio
    async def test_host_no_open_ports(self):
        """Host with no open ports returns None."""
        result = await scan_host("192.0.2.1", [1, 2, 3], fingerprint=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_host_with_mocked_open_ports(self):
        """Mock open ports to verify result structure."""
        async def fake_scan_port(ip, port, fingerprint=True, timeout=1.5):
            if port == 22:
                return {"port": 22, "service": "ssh", "version": "OpenSSH_8.9", "banner": "SSH-2.0-OpenSSH_8.9"}
            if port == 80:
                return {"port": 80, "service": "http", "version": "nginx/1.24", "banner": "HTTP/1.1 200 OK"}
            return None

        with mock.patch("netmap.scanner.scan_port", side_effect=fake_scan_port):
            with mock.patch("netmap.scanner.reverse_dns", return_value="testhost.local"):
                result = await scan_host("10.0.0.1", [22, 80, 443], fingerprint=True)

        assert result is not None
        assert result["ip_address"] == "10.0.0.1"
        assert result["hostname"] == "testhost.local"
        assert result["open_ports"] == [22, 80]
        assert len(result["services"]) == 2
        assert result["services"][0]["service"] == "ssh"
        assert result["services"][1]["service"] == "http"
        assert result["device_type"] == "server"
        assert result["status"] == "online"


# ── scan_network ─────────────────────────────────────────────


class TestScanNetwork:
    @pytest.mark.asyncio
    async def test_empty_network(self):
        """A /32 network has no hosts to scan."""
        results = await scan_network("10.0.0.1/32", [22, 80], fingerprint=False)
        assert results == []

    @pytest.mark.asyncio
    async def test_small_network_mocked(self):
        """Mock scan_host to verify network scanning logic."""
        async def fake_scan_host(ip, ports, fingerprint=True):
            if ip == "10.0.0.1":
                return {
                    "ip_address": ip,
                    "hostname": ip,
                    "open_ports": [22],
                    "services": [{"port": 22, "service": "ssh", "version": "", "banner": ""}],
                    "status": "online",
                    "device_type": "server",
                }
            return None

        with mock.patch("netmap.scanner.scan_host", side_effect=fake_scan_host):
            results = await scan_network("10.0.0.0/30", [22, 80], fingerprint=False)

        # /30 has 2 hosts: .1 and .2, only .1 is "online"
        assert len(results) == 1
        assert results[0]["ip_address"] == "10.0.0.1"


# ── reverse_dns ──────────────────────────────────────────────


class TestReverseDns:
    @pytest.mark.asyncio
    async def test_localhost_reverse(self):
        """Localhost should resolve to something (or return the IP)."""
        result = await reverse_dns("127.0.0.1")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_invalid_ip_returns_ip(self):
        """Non-existent IP should return the IP itself."""
        result = await reverse_dns("192.0.2.1")
        assert result == "192.0.2.1"


# ── DEFAULT_PORTS ────────────────────────────────────────────


def test_default_ports_not_empty():
    assert len(DEFAULT_PORTS) > 0
    assert 22 in DEFAULT_PORTS
    assert 80 in DEFAULT_PORTS
    assert 443 in DEFAULT_PORTS
