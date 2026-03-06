"""Test fixtures."""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from netmap.app import create_app
from netmap.database import Base, get_db
from netmap.models import Device, User  # noqa: F401 — register tables with Base


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_client():
    """Test client backed by an in-memory async SQLite database."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    testing_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create_tables(engine))

    async def override_get_db():
        async with testing_session() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

    loop.run_until_complete(_drop_tables(engine))
    loop.close()


async def _create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
