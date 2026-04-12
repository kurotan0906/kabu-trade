"""Database configuration"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings


def _build_engine_kwargs() -> dict:
    """SSL を無効にすべき接続（Fly.io 内部ネットワーク等）かを判定してエンジン引数を返す"""
    db_url = settings.DATABASE_URL
    kwargs: dict = {"echo": settings.DEBUG, "future": True}
    # URL に ?ssl=false が含まれる場合、asyncpg の connect_args に変換して除去する
    if "ssl=false" in db_url.lower():
        clean_url = db_url.replace("?ssl=false", "").replace("&ssl=false", "")
        kwargs["url"] = clean_url
        kwargs["connect_args"] = {"ssl": False}
    else:
        kwargs["url"] = db_url
    return kwargs


_engine_kwargs = _build_engine_kwargs()
engine = create_async_engine(**_engine_kwargs)

# セッション作成
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    except Exception as e:
        # データベース接続エラーの場合、Noneを返す（データベースなしモード）
        # 実際のセッションが必要な場合はエラーを再発生させる
        raise e
