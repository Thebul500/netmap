"""Pydantic request/response schemas."""

import ipaddress
import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime


# ── Auth schemas ──────────────────────────────────────────────


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Validators ───────────────────────────────────────────────

MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")


def _validate_ip(v: str) -> str:
    """Validate an IPv4 or IPv6 address string."""
    try:
        ipaddress.ip_address(v)
    except ValueError:
        raise ValueError(f"Invalid IP address: {v!r}") from None
    return v


def _validate_mac(v: str | None) -> str | None:
    """Validate a MAC address (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)."""
    if v is None:
        return v
    if not MAC_RE.match(v):
        raise ValueError(f"Invalid MAC address: {v!r} — expected format AA:BB:CC:DD:EE:FF")
    return v.upper()


def _validate_cidr(v: str) -> str:
    """Validate a CIDR notation string (e.g. 192.168.1.0/24)."""
    try:
        ipaddress.ip_network(v, strict=False)
    except ValueError:
        raise ValueError(f"Invalid CIDR: {v!r} — expected format like 192.168.1.0/24") from None
    return v


# ── Device schemas ────────────────────────────────────────────


class DeviceCreate(BaseModel):
    hostname: str
    ip_address: str
    mac_address: str | None = None
    device_type: str | None = "unknown"
    status: str = "online"

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, v: str) -> str:
        return _validate_ip(v)

    @field_validator("mac_address")
    @classmethod
    def check_mac(cls, v: str | None) -> str | None:
        return _validate_mac(v)


class DeviceUpdate(BaseModel):
    hostname: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    device_type: str | None = None
    status: str | None = None

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_ip(v)

    @field_validator("mac_address")
    @classmethod
    def check_mac(cls, v: str | None) -> str | None:
        return _validate_mac(v)


class DeviceResponse(BaseModel):
    id: int
    hostname: str
    ip_address: str
    mac_address: str | None
    device_type: str | None
    status: str
    owner_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Scan schemas ─────────────────────────────────────────────


class ScanCreate(BaseModel):
    target_cidr: str
    ports: str = "22,80,443,8080,8443"

    @field_validator("target_cidr")
    @classmethod
    def check_cidr(cls, v: str) -> str:
        return _validate_cidr(v)


class ScanResponse(BaseModel):
    id: int
    target_cidr: str
    ports: str
    status: str
    device_count: int = 0
    owner_id: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ScanDetailResponse(ScanResponse):
    devices: list[DeviceResponse] = []


# ── Pagination ───────────────────────────────────────────────


class PaginatedDevices(BaseModel):
    items: list[DeviceResponse]
    total: int
    page: int
    page_size: int
    pages: int
