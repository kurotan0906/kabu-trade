# 技術スタック

_updated_at: 2026-01-24_

## アーキテクチャ

- **フロントエンド + API の分離**: UI（React/Vite）とAPI（FastAPI）を分け、HTTPで連携する
- **レイヤード構成（バックエンド）**: API → Service → Repository/External → DB/Cache の責務分離で保守性を確保する
- **非同期I/O前提**: FastAPI + SQLAlchemy(Async) + asyncpg でI/O待ちを効率化する
- **キャッシュ併用**: 頻繁に参照されるデータはRedisを併用し、応答性と外部API負荷を下げる

## コア技術

- **Language**: Python（バックエンド）, TypeScript（フロントエンド）
- **Backend Framework**: FastAPI（uvicorn）
- **Frontend Framework**: React（Vite）
- **DB**: PostgreSQL
- **Cache**: Redis
- **Infra（開発）**: Docker Compose（backend/frontend/postgres/redis を統一起動）

## 主要ライブラリ（開発パターンに影響するもの）

- **API/設定**: FastAPI, pydantic, pydantic-settings
- **DB**: SQLAlchemy 2（Async）, Alembic（マイグレーション）
- **外部通信**: httpx / aiohttp
- **分析**: pandas / numpy / pandas-ta（テクニカル指標）
- **Frontend**: react-router-dom（画面遷移）, zustand（状態管理）, axios（HTTP）

## 開発標準

### 型安全性

- **TypeScript**: `strict: true` を前提に、型の曖昧さを増やさない（`any` 乱用を避ける）
- **Python**: 必要に応じて型注釈を追加し、境界（API入力/外部I/O/DB）で特に慎重に扱う

### コード品質

- **Backend**: black / flake8 / mypy を利用する前提
- **Frontend**: eslint を利用する前提（`npm run lint`）

### テスト

- **Backend**: pytest / pytest-asyncio（非同期テスト）を基本とする
- **Frontend**: 追加予定（現時点は最小構成）
- **テスト収集の安定化**: `backend/pytest.ini` で `.venv` / `venv*` / `site-packages` を除外し、仮想環境内の不要なテスト収集を防ぐ

## 開発環境

### 必須ツール（目安）

- Docker / Docker Compose
- Python（プロジェクトの指示に従う。例: 3.11+）
- Node.js（Vite/TypeScriptが動くバージョン）

### よく使うコマンド

```bash
# 全サービス起動（開発）
docker compose up --build

# DBだけ起動
docker compose up -d postgres redis

# Backend（ローカル起動）
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Lint
cd frontend && npm run lint
```

## 重要な技術的意思決定

- **外部データの切替を前提**: 実サービス（kabuステーション等）とモックの切替ができるように、外部API連携は抽象化（Provider）する
- **UI→APIは `/api` プロキシで統一**: 開発時はViteのproxyで `/api/*` をバックエンドへ転送し、CORSやベースURLの分岐を最小化する
- **“落としどころ”を用意する**: 依存サービス（Redis等）が利用できない場合でも、開発/検証を止めない設計を許容する（ただし機能制限は明示）
- **import-safe を維持する**: `app.services` / `app.repositories` / `app.models` の `__init__.py` は lazy import（`__getattr__`）で、テスト収集やCLI実行時にDB初期化などの重いimportを避ける

---
_標準とパターンを記し、依存パッケージの網羅は避ける_
