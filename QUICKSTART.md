# クイックスタートガイド

Phase 1の機能を最小限の手順で動作確認するためのガイドです。

## 前提条件

- Python 3.11以上
- Node.js 18以上
- Docker & Docker Compose

## 3ステップで起動

### ステップ1: セットアップ（初回のみ）

```bash
./scripts/setup_local.sh
```

このコマンドで以下が自動実行されます：
- 環境チェック（Python, Node.js, Docker）
- バックエンド仮想環境の作成
- 依存関係のインストール
- 環境変数ファイル（.env）の作成
- データベースの初期化（オプション）

### ステップ2: アプリケーション起動

```bash
./scripts/start_dev.sh
```

このコマンドで以下が起動します：
- バックエンドAPI（http://localhost:8000）
- フロントエンド（http://localhost:5173）

### ステップ3: ブラウザで確認

1. ブラウザで http://localhost:5173 を開く
2. 銘柄コード `7203` を入力して検索
3. 銘柄情報とチャートが表示されることを確認

## 動作確認用銘柄コード

モックデータで以下の銘柄が利用可能です：

- `7203` - トヨタ自動車
- `6758` - ソニーグループ
- `9984` - ソフトバンクグループ

## よくある問題と解決方法

### 問題1: セットアップスクリプトが実行できない

```bash
# 実行権限を付与
chmod +x scripts/*.sh
```

### 問題2: データベースが起動しない

```bash
# Dockerが起動しているか確認
docker ps

# データベースを手動で起動
docker compose up -d postgres redis

# マイグレーションを実行
cd backend
source venv/bin/activate
alembic upgrade head
```

### 問題3: バックエンドが起動しない

```bash
# 仮想環境が有効化されているか確認
cd backend
source venv/bin/activate

# 依存関係がインストールされているか確認
pip list | grep fastapi

# 環境変数ファイルが存在するか確認
ls -la .env
```

### 問題4: フロントエンドが起動しない

```bash
# 依存関係を再インストール
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 問題5: チャートが表示されない

1. ブラウザのコンソール（F12）でエラーを確認
2. ネットワークタブでAPIリクエストが成功しているか確認
3. バックエンドのログを確認

## ヘルスチェック

すべてのサービスが正常に動作しているか確認：

```bash
./scripts/health_check.sh
```

## 詳細な手順

より詳細な手順が必要な場合は、以下を参照してください：

- [LOCAL_VERIFICATION_GUIDE.md](./LOCAL_VERIFICATION_GUIDE.md) - 詳細な動作確認ガイド
- [SETUP.md](./SETUP.md) - セットアップ手順
- [LAUNCH_CHECKLIST.md](./LAUNCH_CHECKLIST.md) - ローンチ前チェックリスト

## 次のステップ

動作確認が完了したら：

1. **Phase 2の動作確認**: 評価機能の動作確認
2. **kabuステーションAPIの設定**: 実際のAPIを使用する場合
3. **本番デプロイ**: AWS環境へのデプロイ
