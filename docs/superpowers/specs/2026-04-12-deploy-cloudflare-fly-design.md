# デプロイ設計: Cloudflare Pages + Fly.io（永久無料構成）

_作成日: 2026-04-12_

## 概要

kabu-trade を永久$0で公開するため、Cloudflare Pages（フロントエンド）と Fly.io（バックエンド + DB + Cache）を組み合わせて構成する。個人利用のみを想定。

---

## アーキテクチャ

```
ユーザー
  │
  ├─ [フロントエンド] Cloudflare Pages
  │    - React/Vite の静的ビルド成果物を配信
  │    - GitHub push → 自動ビルド & デプロイ
  │    - 本番 API URL を環境変数 (VITE_API_BASE_URL) で注入
  │
  └─ [バックエンド] Fly.io (Tokyo リージョン: nrt)
       FastAPI コンテナ (既存 backend/Dockerfile 流用)
         │
         ├─ Fly Postgres  (無料枠: 1GB ストレージ)
         └─ Upstash Redis (無料枠: 10,000 コマンド/日)
```

---

## コンポーネント詳細

### フロントエンド: Cloudflare Pages

| 項目 | 内容 |
|---|---|
| ビルドコマンド | `npm run build` |
| 出力ディレクトリ | `dist` |
| Node.js バージョン | 18 以上 |
| 環境変数 | `VITE_API_BASE_URL=https://<appname>.fly.dev` |

**重要な変更点**: 現在、各 API ファイルが `const API_BASE_URL = '/api/v1'` とハードコードしている。Cloudflare Pages では Vite の dev proxy が存在しないため、ビルド時に環境変数でベース URL を注入するよう修正が必要。

修正方針: `frontend/src/lib/apiClient.ts` を新設し、全 API ファイルから共通の axios インスタンスを利用する。

```typescript
// frontend/src/lib/apiClient.ts
const BASE = import.meta.env.VITE_API_BASE_URL ?? '';
export const apiClient = axios.create({ baseURL: `${BASE}/api/v1` });
```

### バックエンド: Fly.io

| 項目 | 内容 |
|---|---|
| リージョン | nrt (東京) |
| VM サイズ | shared-cpu-1x, 256MB RAM (無料枠) |
| Dockerfile | `backend/Dockerfile`（変更なし） |
| 設定ファイル | `fly.toml`（新規作成） |
| ヘルスチェック | `/health` エンドポイント（既存） |

**環境変数（Fly.io Secrets）**:
- `DATABASE_URL` — Fly Postgres の接続文字列（fly postgres attach で自動設定）
- `REDIS_URL` — Upstash Redis の接続文字列
- `CORS_ORIGINS` — `https://<project>.pages.dev`（Cloudflare Pages の URL）
- `USE_MOCK_PROVIDER` — `false`（本番）
- `DEBUG` — `false`

### データベース: Fly Postgres

- `fly postgres create` で作成（shared-cpu-1x, 256MB, 無料枠）
- `fly postgres attach` でバックエンドアプリに接続（`DATABASE_URL` を自動設定）
- Alembic マイグレーションは初回デプロイ後に `fly ssh console` で実行

### キャッシュ: Upstash Redis on Fly.io

- `fly redis create` で Upstash Redis を作成（無料枠: 10,000コマンド/日）
- `fly redis attach` で接続（`REDIS_URL` を自動設定）

---

## デプロイフロー

### 初回セットアップ

```
1. fly auth login
2. fly launch --no-deploy        # fly.toml 生成
3. fly postgres create           # DB 作成
4. fly postgres attach           # DATABASE_URL を自動設定
5. fly redis create              # Redis 作成（Upstash）
6. fly redis attach              # REDIS_URL を自動設定
7. fly secrets set CORS_ORIGINS=https://xxx.pages.dev ...
8. fly deploy                    # バックエンドデプロイ
9. fly ssh console -C "alembic upgrade head"  # マイグレーション
```

### 継続デプロイ

| 対象 | 方法 |
|---|---|
| フロントエンド | GitHub push → Cloudflare Pages が自動ビルド・デプロイ |
| バックエンド | `fly deploy`（手動）または GitHub Actions で自動化 |

---

## 必要なコード変更

| ファイル | 変更内容 |
|---|---|
| `frontend/src/lib/apiClient.ts` | 新規作成: 環境変数ベースの axios インスタンス |
| `frontend/src/services/api/*.ts` | `apiClient` を共通インスタンスから import するよう修正（7ファイル） |
| `fly.toml` | 新規作成: Fly.io デプロイ設定 |
| `docker-compose.prod.yml` | 変更なし（ローカル確認用として保持） |

---

## 無料枠の制約と注意事項

| 項目 | 制限 | 個人利用での影響 |
|---|---|---|
| Fly.io VM | 256MB RAM × 最大3台まで無料 | backend 1台で十分 |
| Fly Postgres | 1GB ストレージ | 株価データ蓄積に注意（適宜 VACUUM） |
| Upstash Redis | 10,000コマンド/日 | キャッシュの TTL 設計に注意 |
| Cloudflare Pages | ビルド500回/月、帯域無制限 | 実質制限なし |

---

## セキュリティ

- Fly.io へのアクセスは HTTPS のみ（Fly が TLS 自動終端）
- 個人利用のため認証機能は現状スコープ外
- 機密情報（DB パスワード等）は `fly secrets set` で管理し、コードにハードコードしない
- `CORS_ORIGINS` に Cloudflare Pages の URL のみ許可

---

## スコープ外

- kabuステーション API 連携（`USE_MOCK_PROVIDER=false` は設定するが、実接続は別途対応）
- 認証・認可（個人利用のため）
- GitHub Actions による fly deploy の自動化（手動デプロイで十分）
- カスタムドメイン設定（`*.pages.dev` と `*.fly.dev` のデフォルト URL を使用）
