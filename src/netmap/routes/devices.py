"""Device CRUD routes."""

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models import Device, User
from ..schemas import DeviceCreate, DeviceResponse, DeviceUpdate, PaginatedDevices

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    body: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = Device(**body.model_dump(), owner_id=current_user.id)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/", response_model=PaginatedDevices)
async def list_devices(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = select(Device).where(Device.owner_id == current_user.id)
    if status_filter:
        base = base.where(Device.status == status_filter)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size).order_by(Device.id))
    items = result.scalars().all()

    return PaginatedDevices(
        items=list(items),  # type: ignore[arg-type]
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.owner_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    body: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.owner_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.owner_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    await db.delete(device)
    await db.commit()
