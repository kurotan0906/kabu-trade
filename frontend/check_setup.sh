#!/bin/bash
# フロントエンド セットアップ確認スクリプト

echo "=================================================="
echo "Kabu Trade フロントエンド セットアップ確認"
echo "=================================================="

# Node.jsバージョン確認
echo ""
echo "1. Node.jsバージョン確認:"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js $NODE_VERSION"
else
    echo "✗ Node.jsがインストールされていません"
    exit 1
fi

# npm確認
echo ""
echo "2. npm確認:"
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✓ npm $NPM_VERSION"
else
    echo "✗ npmがインストールされていません"
    exit 1
fi

# ファイル存在確認
echo ""
echo "3. ファイル存在確認:"
REQUIRED_FILES=(
    "package.json"
    "tsconfig.json"
    "vite.config.ts"
    "src/main.tsx"
    "src/App.tsx"
    "src/pages/HomePage.tsx"
    "src/pages/StockDetailPage.tsx"
    "src/components/stock/StockChart.tsx"
    "src/store/stockStore.ts"
    "src/services/api/stockApi.ts"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (見つかりません)"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo "✗ いくつかのファイルが見つかりません"
    exit 1
fi

# package.jsonの確認
echo ""
echo "4. package.json確認:"
if [ -f "package.json" ]; then
    echo "✓ package.jsonが存在します"
    if [ -d "node_modules" ]; then
        echo "✓ node_modulesが存在します（依存関係がインストール済み）"
    else
        echo "⚠ node_modulesが存在しません（npm installを実行してください）"
    fi
fi

echo ""
echo "=================================================="
echo "✓ 基本的な構造は問題ありません"
echo ""
echo "次のステップ:"
echo "1. 依存関係をインストール: npm install"
echo "2. 開発サーバー起動: npm run dev"
echo "=================================================="
