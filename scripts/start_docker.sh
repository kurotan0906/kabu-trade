#!/bin/bash
# Docker Composeで全サービスを起動するスクリプト

set -e

cd "$(dirname "$0")/.."

echo "=== Docker Composeで全サービスを起動 ==="
echo ""

# 環境変数ファイルの確認
if [ ! -f "backend/.env" ]; then
    echo "警告: backend/.env ファイルが見つかりません"
    echo "SETUP.mdを参照して環境変数を設定してください"
    echo ""
fi

# ビルドと起動
echo "サービスをビルド・起動中..."
docker compose up --build -d

echo ""
echo "=== サービス起動完了 ==="
echo ""
echo "以下のサービスが起動しました:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:5173"
echo ""
echo "ログを確認: docker compose logs -f"
echo "停止: docker compose down"
echo ""

# データベースマイグレーション
echo "データベースマイグレーションを実行中..."
docker compose exec -T backend alembic upgrade head || echo "マイグレーションに失敗しました。バックエンドが起動するまで待ってから再実行してください。"

echo ""
echo "完了！"
