"""Pydantic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


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


# ── Device schemas ────────────────────────────────────────────


class DeviceCreate(BaseModel):
    hostname: str
    ip_address: str
    mac_address: str | None = None
    device_type: str | None = "unknown"
    status: str = "online"


class DeviceUpdate(BaseModel):
    hostname: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    device_type: str | None = None
    status: str | None = None


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
