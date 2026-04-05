"""pytest 設定 - 非同期テスト用の共通設定"""

import pytest
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
import app.core.database as db_module


@pytest.fixture(autouse=True)
def patch_db_engine(monkeypatch):
    """各テストで NullPool エンジンを使用してイベントループ競合を防ぐ"""
    test_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", test_session_factory)
