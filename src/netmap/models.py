"""SQLAlchemy database models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class BaseModel(Base):
    """Abstract base with common fields."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class User(BaseModel):
    """User account for authentication."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    devices: Mapped[list["Device"]] = relationship(back_populates="owner")
    scans: Mapped[list["Scan"]] = relationship(back_populates="owner")


class Scan(BaseModel):
    """A scan job targeting a CIDR range."""

    __tablename__ = "scans"

    target_cidr: Mapped[str] = mapped_column(String(50), nullable=False)
    ports: Mapped[str] = mapped_column(String(500), nullable=False, default="22,80,443,8080,8443")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    device_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="scans")
    devices: Mapped[list["Device"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )


class Device(BaseModel):
    """Discovered network device."""

    __tablename__ = "devices"

    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default="unknown")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="online")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("scans.id"), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="devices")
    scan: Mapped["Scan | None"] = relationship(back_populates="devices")
