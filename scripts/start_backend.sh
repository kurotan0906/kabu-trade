#!/bin/bash
# バックエンド起動スクリプト

set -e

echo "=================================================="
echo "Kabu Trade バックエンド起動"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."
cd backend

# 仮想環境の確認
if [ -z "$VIRTUAL_ENV" ]; then
    echo ""
    echo "仮想環境を有効化中..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "✗ 仮想環境が見つかりません"
        echo "  python -m venv venv を実行してください"
        exit 1
    fi
fi

# 依存関係の確認
echo ""
echo "依存関係を確認中..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠ 依存関係がインストールされていません"
    echo "  pip install -r requirements.txt を実行してください"
    exit 1
fi

# 環境変数ファイルの確認
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠ .envファイルが見つかりません"
    if [ -f ".env.example" ]; then
        echo "  .env.exampleをコピーして.envを作成してください"
        echo "  cp .env.example .env"
    fi
    exit 1
fi

# データベース接続確認
echo ""
echo "データベース接続を確認中..."
if ! docker compose ps postgres | grep -q "Up"; then
    echo "⚠ PostgreSQLが起動していません"
    echo "  ../scripts/init_db.sh を実行してください"
    exit 1
fi

# バックエンド起動
echo ""
echo "バックエンドを起動中..."
echo "  URL: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
