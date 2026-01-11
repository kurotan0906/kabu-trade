#!/bin/bash
# フロントエンド起動スクリプト

set -e

echo "=================================================="
echo "Kabu Trade フロントエンド起動"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."
cd frontend

# Node.jsの確認
if ! command -v node &> /dev/null; then
    echo "✗ Node.jsがインストールされていません"
    exit 1
fi

# npmの確認
if ! command -v npm &> /dev/null; then
    echo "✗ npmがインストールされていません"
    exit 1
fi

# 依存関係の確認
if [ ! -d "node_modules" ]; then
    echo ""
    echo "依存関係をインストール中..."
    npm install
fi

# フロントエンド起動
echo ""
echo "フロントエンドを起動中..."
echo "  URL: http://localhost:5173"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

npm run dev
