# Phase 1 ローンチチェックリスト

## ローンチ前確認事項

### 1. 環境準備 ✅

- [ ] Python 3.11以上がインストールされている
- [ ] Node.js 18以上がインストールされている
- [ ] Docker & Docker Composeがインストールされている
- [ ] Gitリポジトリが最新の状態である

### 2. バックエンド準備 ✅

- [ ] 仮想環境が作成されている（`backend/venv`）
- [ ] 依存関係がインストールされている（`pip install -r requirements.txt`）
- [ ] `.env`ファイルが作成されている（`.env.example`をコピー）
- [ ] `.env`ファイルの設定が正しい（特に`USE_MOCK_PROVIDER=true`を設定）

### 3. フロントエンド準備 ✅

- [ ] 依存関係がインストールされている（`npm install`）
- [ ] `package.json`が正しく設定されている

### 4. データベース準備 ✅

- [ ] Docker ComposeでPostgreSQLとRedisが起動している
- [ ] データベースマイグレーションが実行されている（`alembic upgrade head`）

### 5. 動作確認 ✅

- [ ] バックエンドが起動できる（`http://localhost:8000`）
- [ ] APIドキュメントが表示できる（`http://localhost:8000/docs`）
- [ ] フロントエンドが起動できる（`http://localhost:5173`）
- [ ] 銘柄検索が動作する（モックデータで確認）
- [ ] チャート表示が動作する

## 起動手順

### 方法1: スクリプトを使用（推奨）

```bash
# 1. データベース初期化
./scripts/init_db.sh

# 2. 開発環境起動（バックエンド + フロントエンド）
./scripts/start_dev.sh
```

### 方法2: 手動起動

```bash
# 1. データベース起動
docker compose up -d postgres redis

# 2. データベースマイグレーション
cd backend
source venv/bin/activate
alembic upgrade head

# 3. バックエンド起動（別ターミナル）
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 4. フロントエンド起動（別ターミナル）
cd frontend
npm run dev
```

## 動作確認手順

### 1. バックエンド確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# APIドキュメント確認
open http://localhost:8000/docs
```

### 2. フロントエンド確認

1. ブラウザで `http://localhost:5173` にアクセス
2. 銘柄コードを入力（例: `7203`）
3. 銘柄情報とチャートが表示されることを確認

### 3. モックデータ確認

モックプロバイダーが有効な場合、以下の銘柄コードで動作確認できます：
- `7203` - トヨタ自動車
- `6758` - ソニーグループ
- `9984` - ソフトバンクグループ

## トラブルシューティング

### データベース接続エラー

```bash
# PostgreSQLの状態確認
docker compose ps postgres

# ログ確認
docker compose logs postgres

# 再起動
docker compose restart postgres
```

### Redis接続エラー

```bash
# Redisの状態確認
docker compose ps redis

# ログ確認
docker compose logs redis

# 再起動
docker compose restart redis
```

### バックエンド起動エラー

```bash
# 仮想環境の確認
which python
echo $VIRTUAL_ENV

# 依存関係の再インストール
pip install -r requirements.txt

# 環境変数の確認
cat .env
```

### フロントエンド起動エラー

```bash
# Node.jsバージョン確認
node --version

# 依存関係の再インストール
rm -rf node_modules package-lock.json
npm install
```

### マイグレーションエラー

```bash
# マイグレーション状態確認
alembic current

# マイグレーション履歴確認
alembic history

# 最新までマイグレーション
alembic upgrade head
```

## 本番デプロイ準備

### AWSデプロイ前確認

- [ ] `docker-compose.prod.yml`の設定が正しい
- [ ] 環境変数が本番用に設定されている
- [ ] セキュリティ設定が適切である
- [ ] バックアップ戦略が決まっている

### デプロイ手順（AWS）

1. EC2インスタンスの作成
2. RDSインスタンスの作成
3. S3バケットの作成（フロントエンド用）
4. CloudFrontディストリビューションの作成
5. アプリケーションのデプロイ

詳細は `AWS_ARCHITECTURE.md` を参照してください。

## 次のステップ

Phase 1のローンチが完了したら：

1. Phase 2（評価機能）の動作確認
2. kabuステーションAPIの設定（本番環境用）
3. パフォーマンステスト
4. セキュリティ監査
