#!/bin/bash
# 開発環境起動スクリプト（バックエンドとフロントエンドを同時起動）

set -e

echo "=================================================="
echo "Kabu Trade 開発環境起動"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# データベースの確認
echo ""
echo "データベースの状態を確認中..."
if ! docker compose ps postgres | grep -q "Up"; then
    echo "⚠ データベースが起動していません"
    echo "  データベースを起動しますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        ./scripts/init_db.sh
    else
        echo "  データベースを手動で起動してください: docker compose up -d postgres redis"
        exit 1
    fi
fi

# バックエンドとフロントエンドを別プロセスで起動
echo ""
echo "バックエンドとフロントエンドを起動中..."
echo ""

# バックエンドをバックグラウンドで起動
./scripts/start_backend.sh &
BACKEND_PID=$!

# 少し待ってからフロントエンドを起動
sleep 3
./scripts/start_frontend.sh &
FRONTEND_PID=$!

# プロセス終了を待つ
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
