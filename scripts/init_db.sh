#!/bin/bash
# データベース初期化スクリプト

set -e

echo "=================================================="
echo "Kabu Trade データベース初期化"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# Docker Composeでデータベースを起動
echo ""
echo "1. データベースを起動中..."
docker compose up -d postgres redis

# データベースの起動を待つ
echo ""
echo "2. データベースの起動を待機中..."
sleep 5

# データベース接続確認
echo ""
echo "3. データベース接続確認..."
until docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
  echo "   PostgreSQLの起動を待機中..."
  sleep 2
done
echo "   ✓ PostgreSQLが起動しました"

until docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do
  echo "   Redisの起動を待機中..."
  sleep 2
done
echo "   ✓ Redisが起動しました"

# マイグレーション実行
echo ""
echo "4. データベースマイグレーションを実行中..."
cd backend

# 仮想環境が有効化されているか確認
if [ -z "$VIRTUAL_ENV" ]; then
    echo "   ⚠ 仮想環境が有効化されていません"
    echo "   source venv/bin/activate を実行してください"
    exit 1
fi

# Alembicがインストールされているか確認
if ! command -v alembic &> /dev/null; then
    echo "   ⚠ Alembicがインストールされていません"
    echo "   pip install -r requirements.txt を実行してください"
    exit 1
fi

# マイグレーション実行
alembic upgrade head

echo ""
echo "=================================================="
echo "✓ データベース初期化が完了しました"
echo "=================================================="
