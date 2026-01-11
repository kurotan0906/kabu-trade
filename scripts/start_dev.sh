#!/bin/bash
# 開発環境起動スクリプト（バックエンドとフロントエンドを同時起動）

set -e

echo "=================================================="
echo "Kabu Trade 開発環境起動"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# 環境チェック
echo ""
echo "環境チェック中..."

# バックエンドの環境変数ファイル確認
if [ ! -f "backend/.env" ]; then
    echo "⚠ .envファイルが見つかりません"
    echo "  環境変数ファイルを作成しますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        ./scripts/create_env.sh
    else
        echo "  .envファイルを作成してください: ./scripts/create_env.sh"
        exit 1
    fi
fi

# バックエンドの仮想環境確認
if [ ! -d "backend/venv" ]; then
    echo "⚠ バックエンドの仮想環境が見つかりません"
    echo "  セットアップを実行してください: ./scripts/setup_local.sh"
    exit 1
fi

# フロントエンドの依存関係確認
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠ フロントエンドの依存関係がインストールされていません"
    echo "  セットアップを実行してください: ./scripts/setup_local.sh"
    exit 1
fi

# データベースの確認
echo ""
echo "データベースの状態を確認中..."
if command -v docker &> /dev/null; then
    if ! docker compose ps postgres 2>/dev/null | grep -q "Up"; then
        echo "⚠ データベースが起動していません"
        echo "  データベースを起動しますか？ (y/n)"
        read -r answer
        if [ "$answer" = "y" ]; then
            ./scripts/init_db.sh
        else
            echo "  データベースを手動で起動してください: docker compose up -d postgres redis"
            echo "  続行しますか？ (y/n)"
            read -r answer
            if [ "$answer" != "y" ]; then
                exit 1
            fi
        fi
    else
        echo "  ✓ データベースは起動しています"
    fi
else
    echo "  ⚠ Dockerがインストールされていません（データベースは使用できません）"
fi

# バックエンドとフロントエンドを別プロセスで起動
echo ""
echo "=================================================="
echo "アプリケーションを起動中..."
echo "=================================================="
echo ""
echo "以下のURLでアクセスできます:"
echo "  - フロントエンド: http://localhost:5173"
echo "  - バックエンドAPI: http://localhost:8000"
echo "  - APIドキュメント: http://localhost:8000/docs"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

# バックエンドをバックグラウンドで起動
./scripts/start_backend.sh > /tmp/kabu-trade-backend.log 2>&1 &
BACKEND_PID=$!

# 少し待ってからフロントエンドを起動
sleep 3
./scripts/start_frontend.sh > /tmp/kabu-trade-frontend.log 2>&1 &
FRONTEND_PID=$!

# プロセス終了を待つ
trap "echo ''; echo 'アプリケーションを終了しています...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
