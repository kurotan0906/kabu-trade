"""Database configuration"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings


def _build_engine_kwargs() -> dict:
    """接続 URL を解析し、SSL の有無に応じたエンジン引数を返す"""
    from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

    db_url = settings.DATABASE_URL
    kwargs: dict = {"echo": settings.DEBUG, "future": True}

    if "ssl=false" in db_url.lower():
        clean_url = db_url.replace("?ssl=false", "").replace("&ssl=false", "")
        kwargs["url"] = clean_url
        kwargs["connect_args"] = {"ssl": False}
    else:
        # asyncpg は sslmode=/channel_binding= を URL パラメータとして受け付けない
        parsed = urlparse(db_url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        sslmode = params.pop("sslmode", [None])[0]
        params.pop("channel_binding", None)
        clean_query = urlencode({k: v[0] for k, v in params.items()})
        kwargs["url"] = urlunparse(parsed._replace(query=clean_query))
        if sslmode == "require":
            kwargs["connect_args"] = {"ssl": True}

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
        raise e
