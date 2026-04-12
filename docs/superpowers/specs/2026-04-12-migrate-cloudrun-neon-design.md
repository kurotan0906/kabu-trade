# バックエンド移行設計: Google Cloud Run + Neon PostgreSQL

## 目的

バックエンドのホスティングを Fly.io（有料）から Google Cloud Run + Neon PostgreSQL（永久無料）に移行し、月額 $0 で安定稼働させる。

## 背景

- Fly.io は永久無料枠を 2024 年に廃止。現在は月 $2〜5 の費用が発生する
- Oracle Cloud Always Free は CPU 使用率 20% 未満でインスタンス回収リスクがある
- Cloudflare Workers は asyncpg（C 拡張）が動作しない
- Google Cloud Run + Neon PostgreSQL は永久無料で、重量級 Python ライブラリ（pandas, numpy, yfinance）にも対応可能

## アーキテクチャ

```
ユーザー
  |
  +-- フロントエンド --- Cloudflare Pages（変更なし）
  |                      VITE_API_BASE_URL -> Cloud Run の URL
  |
  +-- バックエンド ----- Google Cloud Run（asia-northeast1 / 東京）
  |                      Docker コンテナ（既存 Dockerfile ベース）
  |                      FastAPI + uvicorn
  |                      min-instances=0, max-instances=1
  |
  +-- DB --------------- Neon PostgreSQL（aws-ap-northeast-1 / 東京）
  |                      asyncpg 接続（SSL 必須）
  |                      0.5GB ストレージ無料枠
  |
  +-- キャッシュ ------- Upstash Redis（変更なし）
```

## コンポーネント詳細

### Google Cloud Run

- リージョン: `asia-northeast1`（東京）
- メモリ: 512MB
- CPU: 1 vCPU
- min-instances: 0（アクセスがない時はスリープ -> コスト $0）
- max-instances: 1（無料枠を超えないため）
- タイムアウト: 300 秒（バッチスコアリング用）
- デプロイ: GitHub リポジトリ連携（Cloud Build）による自動ビルド・デプロイ
- ポート: Cloud Run が注入する `$PORT` 環境変数を使用

#### 無料枠（永久）

- 180,000 vCPU 秒/月（= 約 50 時間 CPU）
- 2,000,000 リクエスト/月
- 1GB ネットワーク送信/月

### Neon PostgreSQL

- リージョン: `aws-ap-northeast-1`（東京）
- ストレージ: 0.5GB（現在のデータは 14MB、十分な余裕）
- コンピュート: 100 CU-hours/月
- 自動サスペンド: 5 分間非アクティブでコンピュートを停止（ストレージは維持）
- 再開: 接続時に自動ウェイクアップ（1〜3 秒）
- SSL: 必須（`sslmode=require`）
- クレカ: 不要

### Upstash Redis（変更なし）

- 月 500K コマンド（永久無料）
- バッチ進捗管理 + 株価キャッシュ用途
- クレカ: 不要

## コード変更

### 変更が必要なファイル

| ファイル | 変更内容 |
|---------|---------|
| `backend/app/core/database.py` | SSL 処理の修正。Neon は SSL 必須のためデフォルト有効にし、`ssl=false` が URL にある場合のみ無効化する形に整理 |
| `backend/alembic/env.py` | 同上（SSL 処理の修正） |
| `backend/Dockerfile` | Cloud Run 向けに `PORT` 環境変数対応 |
| `backend/docker-entrypoint.sh` | uvicorn のポートを `$PORT` から読むように変更 |
| `backend/fly.toml` | 削除 |

### 変更不要

- モデル（`app/models/*`）
- API 層（`app/api/*`）
- サービス層（`app/services/*`）
- リポジトリ層（`app/repositories/*`）
- フロントエンドのコード

### SSL の方針

現在は Fly.io 内部ネットワーク向けに `ssl=false` を検知して SSL を無効にしている。Neon は SSL 必須。ロジックを「SSL はデフォルト有効。`ssl=false` が URL にある場合のみ無効化」に整理する。Neon の接続 URL には `sslmode=require` が含まれるため、特別な処理は不要。

## データ移行

1. ローカル DB から `pg_dump --data-only` でエクスポート
2. Neon に `psql` で直接インポート（外部 TCP 接続可能、Fly.io のようなプロキシ不要）
3. `alembic_version` テーブルは除外（Neon 側で `alembic upgrade head` を実行してスキーマを作成）

## 移行手順

```
1. Neon PostgreSQL を作成し、データを移行
2. Cloud Run にバックエンドをデプロイ
3. 動作確認（Cloud Run URL で直接テスト）
4. Cloudflare Pages の VITE_API_BASE_URL を Cloud Run URL に切り替え
5. フロントエンド再ビルド -> 本番切り替え完了
6. Fly.io のリソースを削除
```

### ダウンタイム

- 手順 1〜3 の間は既存の Fly.io がそのまま稼働
- 手順 4〜5 で切り替え（フロントエンド再ビルドに 1〜2 分）
- 実質的なダウンタイムはほぼゼロ

### ロールバック

手順 6（Fly.io 削除）を実行するまでは、Cloudflare Pages の `VITE_API_BASE_URL` を Fly.io の URL に戻すだけで即座にロールバック可能。

## Fly.io リソースの削除

動作確認完了後に実行:

- `fly apps destroy kabu-trade-backend`
- `fly apps destroy kabu-trade-backend-db`
- リポジトリから `backend/fly.toml` を削除

## コスト

| サービス | 月額 |
|---------|------|
| Cloudflare Pages | $0（永久無料） |
| Google Cloud Run | $0（永久無料枠内） |
| Neon PostgreSQL | $0（永久無料） |
| Upstash Redis | $0（永久無料） |
| **合計** | **$0** |
