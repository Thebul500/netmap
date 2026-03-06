"""SQLAlchemy database models."""


from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class BaseModel(Base):
    """Abstract base with common fields."""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class User(BaseModel):
    """User account for authentication."""

    __tablename__ = "users"

    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    devices = relationship("Device", back_populates="owner")
    scans = relationship("Scan", back_populates="owner")


class Scan(BaseModel):
    """A scan job targeting a CIDR range."""

    __tablename__ = "scans"

    target_cidr = Column(String(50), nullable=False)
    ports = Column(String(500), nullable=False, default="22,80,443,8080,8443")
    status = Column(String(20), nullable=False, default="pending")
    device_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="scans")
    devices = relationship("Device", back_populates="scan", cascade="all, delete-orphan")


class Device(BaseModel):
    """Discovered network device."""

    __tablename__ = "devices"

    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    mac_address = Column(String(17), nullable=True)
    device_type = Column(String(50), nullable=True, default="unknown")
    status = Column(String(20), nullable=False, default="online")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)

    owner = relationship("User", back_populates="devices")
    scan = relationship("Scan", back_populates="devices")
