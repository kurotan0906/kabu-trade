#!/bin/bash
# ヘルスチェックスクリプト

set -e

echo "=================================================="
echo "Kabu Trade ヘルスチェック"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

ALL_OK=true

# 1. データベースチェック
echo ""
echo "1. データベースチェック..."

if command -v docker &> /dev/null; then
    if docker compose ps postgres 2>/dev/null | grep -q "Up"; then
        echo "  ✓ PostgreSQL: 起動中"
        
        # 接続テスト
        if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            echo "  ✓ PostgreSQL: 接続可能"
        else
            echo "  ✗ PostgreSQL: 接続不可"
            ALL_OK=false
        fi
    else
        echo "  ✗ PostgreSQL: 起動していません"
        ALL_OK=false
    fi
    
    if docker compose ps redis 2>/dev/null | grep -q "Up"; then
        echo "  ✓ Redis: 起動中"
        
        # 接続テスト
        if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            echo "  ✓ Redis: 接続可能"
        else
            echo "  ✗ Redis: 接続不可"
            ALL_OK=false
        fi
    else
        echo "  ✗ Redis: 起動していません"
        ALL_OK=false
    fi
else
    echo "  ⚠ Dockerがインストールされていません（スキップ）"
fi

# 2. バックエンドAPIチェック
echo ""
echo "2. バックエンドAPIチェック..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        echo "  ✓ バックエンドAPI: 正常"
        echo "    レスポンス: $HEALTH_RESPONSE"
    else
        echo "  ✗ バックエンドAPI: 異常"
        echo "    レスポンス: $HEALTH_RESPONSE"
        ALL_OK=false
    fi
else
    echo "  ✗ バックエンドAPI: 接続不可（http://localhost:8000 が起動していません）"
    ALL_OK=false
fi

# 3. フロントエンドチェック
echo ""
echo "3. フロントエンドチェック..."

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "  ✓ フロントエンド: アクセス可能"
else
    echo "  ✗ フロントエンド: アクセス不可（http://localhost:5173 が起動していません）"
    ALL_OK=false
fi

# 4. APIエンドポイントチェック
echo ""
echo "4. APIエンドポイントチェック..."

if curl -s http://localhost:8000/api/v1/stocks/7203 > /dev/null 2>&1; then
    STOCK_RESPONSE=$(curl -s http://localhost:8000/api/v1/stocks/7203)
    if echo "$STOCK_RESPONSE" | grep -q "code"; then
        echo "  ✓ 銘柄情報取得API: 正常"
    else
        echo "  ✗ 銘柄情報取得API: 異常"
        echo "    レスポンス: $STOCK_RESPONSE"
        ALL_OK=false
    fi
else
    echo "  ✗ 銘柄情報取得API: 接続不可"
    ALL_OK=false
fi

# 結果表示
echo ""
echo "=================================================="
if [ "$ALL_OK" = true ]; then
    echo "✓ すべてのサービスが正常に動作しています"
    echo ""
    echo "アクセスURL:"
    echo "  - フロントエンド: http://localhost:5173"
    echo "  - バックエンドAPI: http://localhost:8000"
    echo "  - APIドキュメント: http://localhost:8000/docs"
else
    echo "✗ 一部のサービスに問題があります"
    echo ""
    echo "対処方法:"
    echo "  1. データベースが起動していない場合: ./scripts/init_db.sh"
    echo "  2. バックエンドが起動していない場合: ./scripts/start_backend.sh"
    echo "  3. フロントエンドが起動していない場合: ./scripts/start_frontend.sh"
    echo "  4. すべてを起動する場合: ./scripts/start_dev.sh"
fi
echo "=================================================="

if [ "$ALL_OK" = false ]; then
    exit 1
fi
