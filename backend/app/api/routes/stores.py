from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models import Store, DataSource
from app.schemas.store import StoreCreate, StoreRead, DataSourceCreate

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("/", response_model=list[StoreRead])
async def list_stores(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Store).order_by(Store.id))
    return result.scalars().all()


@router.post("/", response_model=StoreRead, status_code=201)
async def create_store(body: StoreCreate, db: AsyncSession = Depends(get_db)):
    store = Store(**body.model_dump())
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return store


@router.get("/{store_id}", response_model=StoreRead)
async def get_store(store_id: int, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(404, "Store not found")
    return store


@router.post("/{store_id}/sources", status_code=201)
async def add_data_source(store_id: int, body: DataSourceCreate, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(404, "Store not found")
    source = DataSource(store_id=store_id, **body.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source
