#!/bin/bash
# 環境変数ファイル自動作成スクリプト

set -e

echo "=================================================="
echo "Kabu Trade 環境変数ファイル作成"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."
cd backend

# .envファイルが既に存在するか確認
if [ -f ".env" ]; then
    echo ""
    echo "⚠ .envファイルが既に存在します"
    echo "  既存のファイルを上書きしますか？ (y/n)"
    read -r answer
    if [ "$answer" != "y" ]; then
        echo "  処理をキャンセルしました"
        exit 0
    fi
    echo "  既存の.envファイルをバックアップします..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# .envファイルを作成
echo ""
echo ".envファイルを作成中..."

cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kabu_trade
REDIS_URL=redis://localhost:6379/0

# kabuステーションAPI
KABU_STATION_API_TOKEN=  # 空欄でOK（自動取得）
KABU_STATION_PASSWORD=your_api_password_here
KABU_STATION_API_URL=https://localhost:18080/kabusapi

# Provider settings
USE_MOCK_PROVIDER=true  # モックプロバイダーを使用する場合はtrue（開発・テスト用）

# Application
APP_NAME=kabu-trade
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF

echo "✓ .envファイルを作成しました"
echo ""
echo "設定内容:"
echo "  - USE_MOCK_PROVIDER=true (モックデータを使用)"
echo "  - DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/kabu_trade"
echo "  - REDIS_URL: redis://localhost:6379/0"
echo ""
echo "⚠ kabuステーションAPIを使用する場合は、.envファイルを編集して"
echo "  USE_MOCK_PROVIDER=false に設定し、KABU_STATION_PASSWORDを設定してください"
