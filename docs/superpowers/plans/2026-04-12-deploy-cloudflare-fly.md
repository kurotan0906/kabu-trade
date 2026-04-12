# Cloudflare Pages + Fly.io デプロイ 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** kabu-trade を Cloudflare Pages（フロントエンド）と Fly.io（バックエンド + DB + Redis）で永久無料デプロイできる状態にする

**Architecture:** フロントエンドは Cloudflare Pages で静的ホスティング。バックエンドは Fly.io の Docker コンテナで動かし、Fly Postgres と Upstash Redis を接続する。各 API ファイルが持つ `/api/v1` のハードコードを環境変数ベースの共通クライアントに統一することで、本番環境からの API 呼び出しを可能にする。

**Tech Stack:** React/Vite (TypeScript), FastAPI (Python 3.11), PostgreSQL, Redis, Fly.io CLI (`flyctl`), Cloudflare Pages (GitHub 連携)

---

## ファイル変更マップ

| 操作 | ファイル | 目的 |
|---|---|---|
| 新規作成 | `frontend/src/lib/apiClient.ts` | 環境変数ベースの共通 axios インスタンス |
| 修正 | `frontend/src/services/api/advisorApi.ts` | 共通クライアントを import |
| 修正 | `frontend/src/services/api/chartAnalysisApi.ts` | 共通クライアントを import |
| 修正 | `frontend/src/services/api/evaluationApi.ts` | 共通クライアントを import |
| 修正 | `frontend/src/services/api/portfolioApi.ts` | 共通クライアントを import |
| 修正 | `frontend/src/services/api/scoresApi.ts` | 共通クライアントを import |
| 修正 | `frontend/src/services/api/stockApi.ts` | 共通クライアントを import |
| 修正 | `frontend/src/services/api/tradingviewApi.ts` | 共通クライアントを import |
| 新規作成 | `backend/fly.toml` | Fly.io デプロイ設定 |

---

## Task 1: 共通 apiClient の作成

**Files:**
- Create: `frontend/src/lib/apiClient.ts`

- [ ] **Step 1: `frontend/src/lib/apiClient.ts` を作成する**

```typescript
// frontend/src/lib/apiClient.ts
import axios from 'axios';

const BASE = import.meta.env.VITE_API_BASE_URL ?? '';

export const apiClient = axios.create({
  baseURL: `${BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});
```

`VITE_API_BASE_URL` が未設定（開発時）なら `''` になり、`baseURL` は `/api/v1` となる。
Vite の dev proxy（`/api → http://backend:8000`）がそのまま動く。
本番では `VITE_API_BASE_URL=https://kabu-trade-backend.fly.dev` を設定する。

- [ ] **Step 2: ビルドが通るか確認する**

```bash
cd frontend
npm run build
```

Expected: `dist/` が生成される（エラーなし）

- [ ] **Step 3: コミット**

```bash
git add frontend/src/lib/apiClient.ts
git commit -m "feat(frontend): add shared apiClient with VITE_API_BASE_URL support"
```

---

## Task 2: 各 API ファイルを共通クライアントに統一（advisorApi）

**Files:**
- Modify: `frontend/src/services/api/advisorApi.ts`

- [ ] **Step 1: `advisorApi.ts` の先頭を修正する**

変更前（1〜12行目付近）:
```typescript
import axios from 'axios';
import type {
  SimulateRequest,
  SimulateResponse,
  RequiredRateResponse,
  HistoryEntry,
} from '@/types/advisor';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});
```

変更後:
```typescript
import { apiClient } from '@/lib/apiClient';
import type {
  SimulateRequest,
  SimulateResponse,
  RequiredRateResponse,
  HistoryEntry,
} from '@/types/advisor';
```

- [ ] **Step 2: lint でエラーがないか確認する**

```bash
cd frontend
npm run lint
```

Expected: エラーなし

- [ ] **Step 3: コミット**

```bash
git add frontend/src/services/api/advisorApi.ts
git commit -m "refactor(frontend): use shared apiClient in advisorApi"
```

---

## Task 3: 各 API ファイルを共通クライアントに統一（残り6ファイル）

**Files:**
- Modify: `frontend/src/services/api/chartAnalysisApi.ts`
- Modify: `frontend/src/services/api/evaluationApi.ts`
- Modify: `frontend/src/services/api/portfolioApi.ts`
- Modify: `frontend/src/services/api/scoresApi.ts`
- Modify: `frontend/src/services/api/stockApi.ts`
- Modify: `frontend/src/services/api/tradingviewApi.ts`

- [ ] **Step 1: `chartAnalysisApi.ts` の先頭を修正する**

変更前:
```typescript
import axios from 'axios';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

変更後:
```typescript
import { apiClient } from '@/lib/apiClient';
```

- [ ] **Step 2: `evaluationApi.ts` の先頭を修正する**

変更前（先頭付近）:
```typescript
import axios from 'axios';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

変更後:
```typescript
import { apiClient } from '@/lib/apiClient';
```

- [ ] **Step 3: `portfolioApi.ts` の先頭を修正する**

変更前:
```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});
```

変更後:
```typescript
import { apiClient } from '@/lib/apiClient';
```

- [ ] **Step 4: `scoresApi.ts` の先頭を修正する**

変更前:
```typescript
import axios from 'axios';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

変更後:
```typescript
import { apiClient } from '@/lib/apiClient';
```

- [ ] **Step 5: `stockApi.ts` の先頭を修正する**

変更前:
```typescript
import axios from 'axios';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

変更後:
```typescript
import { apiClient } from '@/lib/apiClient';
```

- [ ] **Step 6: `tradingviewApi.ts` の先頭を修正する**

変更前:
```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});
```

変更後:
```typescript
import { apiClient } from '@/lib/apiClient';
```

- [ ] **Step 7: lint とビルドで確認する**

```bash
cd frontend
npm run lint && npm run build
```

Expected: エラーなし、`dist/` が生成される

- [ ] **Step 8: コミット**

```bash
git add frontend/src/services/api/
git commit -m "refactor(frontend): unify all API files to use shared apiClient"
```

---

## Task 4: Fly.io 設定ファイルの作成

**Files:**
- Create: `backend/fly.toml`

- [ ] **Step 1: `flyctl` がインストールされているか確認する**

```bash
fly version
```

未インストールの場合はインストールする:
```bash
brew install flyctl
```

- [ ] **Step 2: `backend/fly.toml` を作成する**

`<YOUR_APP_NAME>` は Fly.io 上でユニークな名前（例: `kabu-trade-backend-masayuki`）に変えること。

```toml
# backend/fly.toml
app = "<YOUR_APP_NAME>"
primary_region = "nrt"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

`min_machines_running = 1` で常時起動（無料枠 3VM 以内）。
`auto_stop_machines = true` でアイドル時はスリープし、アクセス時に自動起動する（コスト節約）。

- [ ] **Step 3: コミット**

```bash
git add backend/fly.toml
git commit -m "feat(infra): add fly.toml for Fly.io deployment"
```

---

## Task 5: Fly.io バックエンドの初回デプロイ

**注意:** このタスクは CLI 操作のみ。コードの変更はない。`backend/` ディレクトリで実行すること。

- [ ] **Step 1: Fly.io にログインする**

```bash
fly auth login
```

ブラウザが開く。アカウント未作成の場合は https://fly.io でサインアップ（クレカ登録なしで無料枠利用可）。

- [ ] **Step 2: アプリを作成する（デプロイはまだしない）**

```bash
cd backend
fly launch --no-deploy
```

対話式プロンプトが出る:
- `App Name`: `fly.toml` に書いた `<YOUR_APP_NAME>` を入力
- `Region`: `nrt` (Tokyo) を選択
- `Would you like to set up a Postgresql database?`: `No`（後で手動で作成）
- `Would you like to set up an Upstash Redis database?`: `No`（後で手動で作成）

既存の `fly.toml` を上書きするか聞かれた場合は `No`（既存を使う）。

- [ ] **Step 3: Fly Postgres を作成してアタッチする**

```bash
fly postgres create --name <YOUR_APP_NAME>-db --region nrt --vm-size shared-cpu-1x --volume-size 1
fly postgres attach <YOUR_APP_NAME>-db
```

`fly postgres attach` 実行後、`DATABASE_URL` が自動的に Secret として設定される。
ただし URL は `postgres://...` 形式なので、FastAPI が使う `postgresql+asyncpg://...` に変換が必要。

```bash
# 現在の DATABASE_URL を確認
fly secrets list

# asyncpg 用に上書き（postgres:// → postgresql+asyncpg:// に変換）
# fly secrets list で表示された DATABASE_URL の値を元に変換する
fly secrets set DATABASE_URL="postgresql+asyncpg://<user>:<password>@<host>/<dbname>?ssl=require"
```

> 接続文字列の `<user>`, `<password>`, `<host>`, `<dbname>` は `fly secrets list` / `fly postgres connect` で確認できる。
> または `fly postgres attach` の出力に表示される。

- [ ] **Step 4: Upstash Redis を作成してアタッチする**

```bash
fly redis create --name <YOUR_APP_NAME>-redis --region nrt --plan free
fly redis attach <YOUR_APP_NAME>-redis
```

`REDIS_URL` が自動的に Secret として設定される。

- [ ] **Step 5: 残りの環境変数を設定する**

`<CLOUDFLARE_PAGES_URL>` は後で Cloudflare Pages のデプロイ後に確定する。
先に仮の値で設定し、Task 6 完了後に更新する。

```bash
fly secrets set \
  CORS_ORIGINS="https://<YOUR_PROJECT>.pages.dev" \
  USE_MOCK_PROVIDER="false" \
  DEBUG="false" \
  LOG_LEVEL="INFO" \
  SCORING_MAX_WORKERS="1" \
  SCORING_YFINANCE_MIN_INTERVAL_SEC="0.35"
```

- [ ] **Step 6: デプロイする**

```bash
fly deploy
```

Expected: ビルドが完了し `✓ Machine created` と表示される。数分かかる。

- [ ] **Step 7: ヘルスチェックで動作確認する**

```bash
fly status
curl https://<YOUR_APP_NAME>.fly.dev/health
```

Expected: `{"status": "ok"}` または同等のレスポンス

- [ ] **Step 8: Alembic マイグレーションを実行する**

```bash
fly ssh console -C "alembic upgrade head"
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade ...` のようなログが表示される

---

## Task 6: Cloudflare Pages のセットアップとフロントエンドデプロイ

**注意:** このタスクは Cloudflare ダッシュボードでの操作。コードの変更はない。
前提: GitHub にコードが push されていること（Tasks 1〜4 のコミット済み）。

- [ ] **Step 1: Cloudflare アカウントを作成する（未作成の場合）**

https://dash.cloudflare.com にアクセスしてサインアップ（無料）。

- [ ] **Step 2: Pages プロジェクトを作成する**

1. Cloudflare ダッシュボード → `Workers & Pages` → `Create application`
2. `Pages` タブ → `Connect to Git`
3. GitHub アカウントを連携し、`kabu-trade` リポジトリを選択
4. `Begin setup` をクリック

- [ ] **Step 3: ビルド設定を入力する**

| 項目 | 値 |
|---|---|
| Project name | `kabu-trade`（任意） |
| Production branch | `main` |
| Framework preset | `None`（Vite は手動設定） |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Root directory | `frontend` |

- [ ] **Step 4: 環境変数を設定する**

`Environment variables` セクションで追加:

| 変数名 | 値 |
|---|---|
| `VITE_API_BASE_URL` | `https://<YOUR_APP_NAME>.fly.dev` |
| `NODE_VERSION` | `18` |

- [ ] **Step 5: `Save and Deploy` をクリックする**

初回ビルドが走る（2〜3分）。

Expected: `https://kabu-trade.pages.dev`（または設定した名前）でフロントエンドが表示される

- [ ] **Step 6: 動作確認する**

1. ブラウザで `https://kabu-trade.pages.dev` を開く
2. 銘柄検索など基本操作が動くことを確認
3. ブラウザの DevTools → Network タブで `/api/v1/...` へのリクエストが `https://<YOUR_APP_NAME>.fly.dev` に飛んでいることを確認

- [ ] **Step 7: バックエンドの CORS_ORIGINS を確定した URL で更新する**

Cloudflare Pages の実際の URL（例: `https://kabu-trade-abc.pages.dev`）が確定したら:

```bash
cd backend
fly secrets set CORS_ORIGINS="https://kabu-trade-abc.pages.dev"
fly deploy
```

---

## 動作確認チェックリスト（全タスク完了後）

- [ ] `https://<project>.pages.dev` でフロントエンドが表示される
- [ ] 銘柄検索が動く（API 呼び出しが成功している）
- [ ] `fly logs` でエラーが出ていない
- [ ] `fly status` で Machine が `started` になっている
- [ ] `curl https://<YOUR_APP_NAME>.fly.dev/health` が正常レスポンスを返す
