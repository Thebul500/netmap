"""Scan management routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import get_current_user
from ..database import async_session, get_db
from ..models import Device, Scan, User
from ..scanner import parse_ports, scan_network
from ..schemas import ScanCreate, ScanDetailResponse, ScanResponse

router = APIRouter(prefix="/scans", tags=["scans"])


async def _run_scan(scan_id: int, target_cidr: str, ports_str: str, owner_id: int) -> None:
    """Background task: execute the scan and persist results."""
    async with async_session() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan is None:
            return

        scan.status = "running"
        scan.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            ports = parse_ports(ports_str)
            discovered = await scan_network(target_cidr, ports)

            for device_data in discovered:
                device = Device(
                    hostname=device_data["hostname"],
                    ip_address=device_data["ip_address"],
                    mac_address=None,
                    device_type=device_data.get("device_type", "unknown"),
                    status="online",
                    owner_id=owner_id,
                    scan_id=scan_id,
                )
                db.add(device)

            scan.device_count = len(discovered)
            scan.status = "completed"
            scan.finished_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as exc:
            scan.status = "failed"
            scan.error_message = str(exc)[:1000]
            scan.finished_at = datetime.now(timezone.utc)
            await db.commit()


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    body: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = Scan(
        target_cidr=body.target_cidr,
        ports=body.ports,
        status="pending",
        owner_id=current_user.id,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    background_tasks.add_task(_run_scan, scan.id, body.target_cidr, body.ports, current_user.id)

    return scan


@router.get("/", response_model=list[ScanResponse])
async def list_scans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan).where(Scan.owner_id == current_user.id).order_by(Scan.id.desc())
    )
    return result.scalars().all()


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan)
        .options(selectinload(Scan.devices))
        .where(Scan.id == scan_id, Scan.owner_id == current_user.id)
    )
    scan = result.scalar_one_or_none()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return scan


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id, Scan.owner_id == current_user.id)
    )
    scan = result.scalar_one_or_none()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    await db.delete(scan)
    await db.commit()
