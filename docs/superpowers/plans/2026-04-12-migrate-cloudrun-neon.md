# Cloud Run + Neon PostgreSQL 移行 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** バックエンド+DBを Fly.io から Google Cloud Run + Neon PostgreSQL に移行し、月額 $0 で稼働させる。

**Architecture:** 既存の FastAPI + SQLAlchemy (asyncpg) コードベースを最小限の変更で Cloud Run に移行する。DB は Neon PostgreSQL（SSL 必須）に切り替え、データは pg_dump/psql で移行する。フロントエンド（Cloudflare Pages）と Redis（Upstash）は変更なし。

**Tech Stack:** Google Cloud Run, Neon PostgreSQL, Docker, FastAPI, SQLAlchemy, asyncpg, Alembic

---

## ファイル構成

| ファイル | 操作 | 責務 |
|---------|------|------|
| `backend/docker-entrypoint.sh` | 修正 | Cloud Run の `$PORT` 環境変数に対応 |
| `backend/Dockerfile` | 修正 | `EXPOSE` を `$PORT` 対応に変更 |
| `backend/app/core/database.py` | 修正 | SSL 処理を整理（デフォルト有効、`ssl=false` で無効化） |
| `backend/alembic/env.py` | 修正 | SSL 処理を整理（database.py と同じ方針） |
| `backend/fly.toml` | 削除 | Fly.io 固有の設定ファイル |

---

### Task 1: docker-entrypoint.sh を Cloud Run 対応に修正

**Files:**
- Modify: `backend/docker-entrypoint.sh`

- [ ] **Step 1: docker-entrypoint.sh を修正**

Cloud Run は `$PORT` 環境変数でリスニングポートを注入する。uvicorn がこのポートを使うように変更する。ローカル開発ではデフォルト 8000 を使う。

```sh
#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

- [ ] **Step 2: ローカルで動作確認**

Run: `PORT=9000 ./docker-entrypoint.sh`
Expected: uvicorn がポート 9000 で起動する（Ctrl+C で停止）

Run: `./docker-entrypoint.sh`
Expected: uvicorn がデフォルトのポート 8000 で起動する（Ctrl+C で停止）

- [ ] **Step 3: コミット**

```bash
git add backend/docker-entrypoint.sh
git commit -m "fix(infra): use PORT env var in entrypoint for Cloud Run compatibility"
```

---

### Task 2: Dockerfile を Cloud Run 向けに調整

**Files:**
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Dockerfile を修正**

`EXPOSE 8000` を削除し（Cloud Run は `$PORT` を使うため固定ポートは不要）、`CMD` はそのまま。

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# システム依存関係のインストール（ビルド用）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 本番用イメージ
FROM python:3.11-slim

WORKDIR /app

# システム依存関係のインストール（最小限）
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージから依存関係をコピー
COPY --from=builder /root/.local /root/.local

# パスに追加
ENV PATH=/root/.local/bin:$PATH

# アプリケーションコードのコピー
COPY . .

# エントリーポイントスクリプトに実行権限を付与
RUN chmod +x docker-entrypoint.sh

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# 起動時にマイグレーションを実行してからアプリを起動
CMD ["./docker-entrypoint.sh"]
```

変更点:
- `EXPOSE 8000` を削除
- `HEALTHCHECK` の URL を `${PORT:-8000}` に変更

- [ ] **Step 2: Docker ビルドが通ることを確認**

Run: `cd backend && docker build -t kabu-trade-backend:test .`
Expected: ビルド成功

- [ ] **Step 3: コミット**

```bash
git add backend/Dockerfile
git commit -m "fix(infra): remove fixed EXPOSE and use PORT env in healthcheck for Cloud Run"
```

---

### Task 3: database.py の SSL 処理を整理

**Files:**
- Modify: `backend/app/core/database.py`

- [ ] **Step 1: database.py を修正**

Neon PostgreSQL は SSL 必須。現在の `ssl=false` 検知ロジックを「デフォルト SSL 有効、`ssl=false` が URL にある場合のみ無効化」に整理する。

```python
"""Database configuration"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings


def _build_engine_kwargs() -> dict:
    """接続 URL を解析し、SSL の有無に応じたエンジン引数を返す"""
    db_url = settings.DATABASE_URL
    kwargs: dict = {"echo": settings.DEBUG, "future": True}

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
        raise e
```

変更点: コメントを日本語から簡潔な説明に修正。ロジック自体は変更なし — Neon の URL には `ssl=false` が含まれないため、SSL 有効（asyncpg デフォルト）のまま接続される。Fly.io 内部ネットワーク用に `ssl=false` 分岐を残す（ローカル開発互換のため）。

- [ ] **Step 2: ローカル DB に接続できることを確認**

Run: `cd backend && python -c "from app.core.database import engine; print(engine.url)"`
Expected: `postgresql+asyncpg://postgres:***@localhost:5432/kabu_trade` が表示される

- [ ] **Step 3: コミット**

```bash
git add backend/app/core/database.py
git commit -m "refactor(db): clean up SSL handling comments in database.py"
```

---

### Task 4: alembic/env.py の SSL 処理を整理

**Files:**
- Modify: `backend/alembic/env.py`

- [ ] **Step 1: alembic/env.py を修正**

database.py と同じ方針で SSL を処理する。変更はコメントの整理のみ。ロジックは変更なし。

```python
"""Alembic environment configuration"""

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base and models
from app.core.database import Base
from app.models.stock import Stock  # noqa: F401
from app.models.stock_price import StockPrice  # noqa: F401
from app.models.evaluation import Evaluation  # noqa: F401
from app.models.investment_strategy import InvestmentStrategy  # noqa: F401
from app.models.key_point import KeyPoint  # noqa: F401

# Set target metadata
target_metadata = Base.metadata

# Get database URL from environment variable or use config file
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get DATABASE_URL from environment, fallback to config file
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
else:
    config.set_main_option("sqlalchemy.url", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    raw_url = config.get_main_option("sqlalchemy.url")

    connect_args = {}
    if "ssl=false" in raw_url.lower():
        raw_url = raw_url.replace("?ssl=false", "").replace("&ssl=false", "")
        connect_args["ssl"] = False

    configuration["sqlalchemy.url"] = raw_url
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
```

変更点: コメントの整理のみ。ロジックは変更なし。

- [ ] **Step 2: マイグレーションが実行できることを確認**

Run: `cd backend && alembic current`
Expected: 現在のリビジョンが表示される

- [ ] **Step 3: コミット**

```bash
git add backend/alembic/env.py
git commit -m "refactor(db): clean up SSL handling comments in alembic env"
```

---

### Task 5: fly.toml を削除

**Files:**
- Delete: `backend/fly.toml`

- [ ] **Step 1: fly.toml を削除**

```bash
git rm backend/fly.toml
```

- [ ] **Step 2: コミット**

```bash
git commit -m "chore(infra): remove fly.toml (migrating to Cloud Run)"
```

---

### Task 6: Neon PostgreSQL をセットアップしデータを移行

**Files:** なし（外部サービスのセットアップとデータ移行）

- [ ] **Step 1: Neon でプロジェクトを作成**

1. https://console.neon.tech にアクセスし、アカウントを作成（GitHub 認証可）
2. 「New Project」をクリック
3. 設定:
   - Project name: `kabu-trade`
   - Region: `AWS ap-northeast-1 (Tokyo)`
   - Database name: `kabu_trade_backend`
   - Role name: デフォルト（`neondb_owner` または指定のもの）
4. 作成後、**Connection string** をコピーする（`postgresql://user:pass@ep-xxx.ap-northeast-1.aws.neon.tech/kabu_trade_backend?sslmode=require`）

- [ ] **Step 2: 接続文字列を asyncpg 形式に変換**

Neon の接続文字列をコピーし、`postgresql://` を `postgresql+asyncpg://` に変換する。

例:
```
postgresql+asyncpg://user:pass@ep-xxx.ap-northeast-1.aws.neon.tech/kabu_trade_backend?sslmode=require
```

- [ ] **Step 3: Alembic でスキーマを作成**

Neon の接続文字列を `DATABASE_URL` 環境変数に設定し、マイグレーションを実行する。

```bash
cd backend
DATABASE_URL="postgresql+asyncpg://user:pass@ep-xxx.ap-northeast-1.aws.neon.tech/kabu_trade_backend?sslmode=require" alembic upgrade head
```

Expected: `INFO [alembic.runtime.migration] Running upgrade -> ...` が表示される

- [ ] **Step 4: ローカル DB からデータをエクスポート**

```bash
docker exec kabu-trade-postgres pg_dump -U postgres --data-only --disable-triggers --no-owner --exclude-table=alembic_version kabu_trade > /tmp/kabu_dump.sql
```

Expected: `/tmp/kabu_dump.sql` が生成される（約 20,000 行）

- [ ] **Step 5: Neon にデータをインポート**

Neon の接続文字列（`postgresql+asyncpg://` ではなく `postgresql://` 形式）を使って psql でインポートする。

```bash
psql "postgresql://user:pass@ep-xxx.ap-northeast-1.aws.neon.tech/kabu_trade_backend?sslmode=require" < /tmp/kabu_dump.sql
```

注: ローカルに `psql` がない場合は Docker 経由:

```bash
docker run --rm -i -v /tmp/kabu_dump.sql:/dump.sql postgres:17-alpine \
  psql "postgresql://user:pass@ep-xxx.ap-northeast-1.aws.neon.tech/kabu_trade_backend?sslmode=require" \
  -f /dump.sql
```

Expected: `COPY N` が各テーブルに対して表示される

- [ ] **Step 6: データの確認**

```bash
docker run --rm postgres:17-alpine \
  psql "postgresql://user:pass@ep-xxx.ap-northeast-1.aws.neon.tech/kabu_trade_backend?sslmode=require" \
  -c "SELECT COUNT(*) FROM stocks; SELECT COUNT(*) FROM stock_prices; SELECT COUNT(*) FROM holdings;"
```

Expected: ローカルと同じ件数（stocks: 1, stock_prices: 265, holdings: 5）

---

### Task 7: Google Cloud Run にデプロイ

**Files:** なし（GCP コンソール / gcloud CLI での操作）

- [ ] **Step 1: GCP プロジェクトを作成**

1. https://console.cloud.google.com にアクセス
2. 新しいプロジェクトを作成（例: `kabu-trade`）
3. Cloud Run API と Cloud Build API を有効化:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

- [ ] **Step 2: gcloud CLI でプロジェクトを設定**

```bash
gcloud config set project <PROJECT_ID>
gcloud config set run/region asia-northeast1
```

- [ ] **Step 3: Docker イメージをビルドしてデプロイ**

```bash
cd backend
gcloud run deploy kabu-trade-backend \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --timeout 300 \
  --set-env-vars "DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.ap-northeast-1.aws.neon.tech/kabu_trade_backend?sslmode=require" \
  --set-env-vars "REDIS_URL=rediss://default:xxx@in-toucan-96937.upstash.io:6379" \
  --set-env-vars "CORS_ORIGINS=https://kabu-trade.pages.dev" \
  --set-env-vars "USE_MOCK_PROVIDER=true" \
  --set-env-vars "SCORING_DATA_SOURCE=hybrid" \
  --set-env-vars "SCORING_MAX_WORKERS=1" \
  --set-env-vars "SCORING_YFINANCE_MIN_INTERVAL_SEC=1.0"
```

Expected: `Service [kabu-trade-backend] revision [kabu-trade-backend-xxxxx] has been deployed and is serving 100 percent of traffic.` と URL が表示される

- [ ] **Step 4: ヘルスチェック**

```bash
curl https://kabu-trade-backend-xxxxx.asia-northeast1.run.app/health
```

Expected: `{"status":"healthy"}`

- [ ] **Step 5: API の動作確認**

```bash
curl https://kabu-trade-backend-xxxxx.asia-northeast1.run.app/api/v1/scores/ranking
```

Expected: スコアデータの JSON が返る

---

### Task 8: フロントエンドの接続先を切り替え

**Files:** なし（Cloudflare Pages の環境変数変更）

- [ ] **Step 1: Cloudflare Pages の環境変数を更新**

Cloudflare Dashboard → Pages → `kabu-trade` → Settings → Environment variables:

| 変数名 | 新しい値 |
|--------|---------|
| `VITE_API_BASE_URL` | `https://kabu-trade-backend-xxxxx.asia-northeast1.run.app` |

（`xxxxx` は Cloud Run が割り当てた実際の URL に置き換える）

- [ ] **Step 2: フロントエンドを再ビルド**

Cloudflare Pages → Deployments → 最新デプロイの `...` → Retry deployment

Expected: ビルド成功

- [ ] **Step 3: エンドツーエンド動作確認**

ブラウザで `https://kabu-trade.pages.dev` を開く。

確認項目:
1. ダッシュボードが表示される
2. ランキングページにスコアデータが表示される
3. ポートフォリオページに保有銘柄が表示される
4. 検索が動作する

- [ ] **Step 4: ロールバック不要を確認**

全ての機能が正常に動作することを確認したら、次の Task に進む。問題があれば `VITE_API_BASE_URL` を Fly.io の URL（`https://kabu-trade-backend.fly.dev`）に戻して Retry deployment でロールバック可能。

---

### Task 9: Fly.io リソースを削除

**Files:**
- Already deleted: `backend/fly.toml`（Task 5 で削除済み）

- [ ] **Step 1: Fly.io バックエンドアプリを削除**

```bash
fly apps destroy kabu-trade-backend --yes
```

Expected: `kabu-trade-backend has been destroyed`

- [ ] **Step 2: Fly.io PostgreSQL を削除**

```bash
fly apps destroy kabu-trade-backend-db --yes
```

Expected: `kabu-trade-backend-db has been destroyed`

- [ ] **Step 3: 最終確認**

ブラウザで `https://kabu-trade.pages.dev` を開き、引き続き正常に動作することを確認する。

- [ ] **Step 4: コミットとプッシュ**

Task 1〜5 の変更がすべてプッシュされていることを確認:

```bash
git push origin main
```
