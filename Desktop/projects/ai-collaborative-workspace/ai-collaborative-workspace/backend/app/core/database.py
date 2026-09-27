from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/workspace_db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/workspace_db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Turn off detailed query logging in performance runs
    future=True,
    pool_size=20,         # Maximum persistent connections in the pool
    max_overflow=10,      # Allowed temporary burst connections beyond pool_size
    pool_timeout=30,      # Seconds to wait before throwing timeout error
    pool_recycle=1800     # Recycle connections every 30 minutes
)