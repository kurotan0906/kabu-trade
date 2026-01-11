# Phase 1 動作確認ステップ

## 現在の状況

### ✅ 完了した項目
- バックエンド仮想環境の作成
- 主要な依存関係のインストール
- 環境変数ファイル（.env）の作成
- アプリケーションコードの修正（CORS設定、Redis接続エラーハンドリング）

### ⚠️ 必要な項目
- Node.jsのインストール（フロントエンド用）
- Dockerのインストール（データベース用、オプション）

## 動作確認手順

### オプション1: バックエンドAPIのみで動作確認

データベースなしでも、モックデータでAPIの動作確認が可能です：

```bash
# 1. バックエンドを起動
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**確認方法:**
1. ブラウザで http://localhost:8000/docs にアクセス
2. `/api/v1/stocks/{code}` エンドポイントを試す
   - `code`: `7203`（トヨタ自動車）
3. レスポンスが返ることを確認

### オプション2: 完全な動作確認（推奨）

Node.jsとDockerをインストール後：

```bash
# 1. セットアップ（初回のみ）
./scripts/setup_local.sh

# 2. アプリケーション起動
./scripts/start_dev.sh

# 3. ブラウザで確認
# http://localhost:5173 にアクセス
```

## 現在の環境状況

- Python: 3.9.6 ✅
- バックエンド依存関係: インストール済み ✅
- 環境変数ファイル: 作成済み ✅
- Node.js: 未インストール ⚠️
- Docker: 未インストール ⚠️

## 次のステップ

### Node.jsをインストールする場合

macOS:
```bash
brew install node
```

または、[Node.js公式サイト](https://nodejs.org/)からダウンロード

### Dockerをインストールする場合

[Docker Desktop](https://www.docker.com/products/docker-desktop)からダウンロード

## バックエンドAPIの動作確認（データベースなし）

以下のコマンドでバックエンドを起動できます：

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

起動後、ブラウザで以下にアクセス：
- APIドキュメント: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/health

APIドキュメントから直接APIを試すことができます。
