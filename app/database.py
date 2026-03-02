from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import TypeVar

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, declarative_base

from config import config


async_engine: AsyncEngine = create_async_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
Base = declarative_base()

T = TypeVar("T")


@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


async def run_db(fn: Callable[[Session], T], *args, **kwargs) -> T:
    async with AsyncSessionLocal() as db:
        return await db.run_sync(lambda sync_db: fn(sync_db, *args, **kwargs))
