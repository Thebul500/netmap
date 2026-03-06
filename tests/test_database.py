"""Tests for database module."""

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from netmap.database import Base, async_session, engine, get_db


def test_engine_is_async():
    """Engine is an async SQLAlchemy engine."""
    assert isinstance(engine, AsyncEngine)


def test_async_session_factory():
    """async_session is a session maker that produces AsyncSession."""
    assert isinstance(async_session, async_sessionmaker)


def test_base_is_declarative():
    """Base is a SQLAlchemy DeclarativeBase subclass."""
    assert issubclass(Base, DeclarativeBase)


@pytest.mark.asyncio
async def test_get_db_yields_session():
    """get_db yields an AsyncSession and closes it."""
    gen = get_db()
    session = await gen.__anext__()
    assert isinstance(session, AsyncSession)
    # Cleanup: exhaust the generator
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()
