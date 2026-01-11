#!/bin/bash
# 統合セットアップスクリプト

set -e

echo "=================================================="
echo "Kabu Trade ローカル環境セットアップ"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# 1. 環境チェック
echo ""
echo "1. 環境チェック中..."

# Pythonチェック
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3がインストールされていません"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "  ✓ Python: $PYTHON_VERSION"

# Node.jsチェック
if ! command -v node &> /dev/null; then
    echo "✗ Node.jsがインストールされていません"
    exit 1
fi
NODE_VERSION=$(node --version)
echo "  ✓ Node.js: $NODE_VERSION"

# npmチェック
if ! command -v npm &> /dev/null; then
    echo "✗ npmがインストールされていません"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo "  ✓ npm: $NPM_VERSION"

# Dockerチェック
if ! command -v docker &> /dev/null; then
    echo "⚠ Dockerがインストールされていません（データベース起動に必要）"
    echo "  Docker Desktopをインストールしてください: https://www.docker.com/products/docker-desktop"
    read -p "  続行しますか？ (y/n): " answer
    if [ "$answer" != "y" ]; then
        exit 1
    fi
else
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo "  ✓ Docker: $DOCKER_VERSION"
fi

# 2. バックエンドセットアップ
echo ""
echo "2. バックエンドセットアップ中..."

cd backend

# 仮想環境の作成
if [ ! -d "venv" ]; then
    echo "  仮想環境を作成中..."
    python3 -m venv venv
    echo "  ✓ 仮想環境を作成しました"
else
    echo "  ✓ 仮想環境は既に存在します"
fi

# 仮想環境を有効化
echo "  仮想環境を有効化中..."
source venv/bin/activate

# 依存関係のインストール
echo "  依存関係をインストール中..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "  ✓ バックエンドの依存関係をインストールしました"

# 環境変数ファイルの作成
if [ ! -f ".env" ]; then
    echo ""
    echo "  環境変数ファイルを作成中..."
    cd ..
    ./scripts/create_env.sh
    cd backend
else
    echo "  ✓ .envファイルは既に存在します"
fi

cd ..

# 3. フロントエンドセットアップ
echo ""
echo "3. フロントエンドセットアップ中..."

cd frontend

# 依存関係のインストール
if [ ! -d "node_modules" ]; then
    echo "  依存関係をインストール中..."
    npm install
    echo "  ✓ フロントエンドの依存関係をインストールしました"
else
    echo "  ✓ フロントエンドの依存関係は既にインストール済みです"
fi

cd ..

# 4. データベース初期化
echo ""
echo "4. データベース初期化中..."

if command -v docker &> /dev/null; then
    echo "  データベースを初期化しますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        ./scripts/init_db.sh
    else
        echo "  データベース初期化をスキップしました"
        echo "  後で ./scripts/init_db.sh を実行してください"
    fi
else
    echo "  ⚠ Dockerがインストールされていないため、データベース初期化をスキップします"
    echo "  Dockerをインストール後、./scripts/init_db.sh を実行してください"
fi

# 5. セットアップ完了
echo ""
echo "=================================================="
echo "✓ セットアップが完了しました！"
echo "=================================================="
echo ""
echo "次のステップ:"
echo "1. データベースを初期化（まだの場合）:"
echo "   ./scripts/init_db.sh"
echo ""
echo "2. アプリケーションを起動:"
echo "   ./scripts/start_dev.sh"
echo ""
echo "3. ブラウザでアクセス:"
echo "   - フロントエンド: http://localhost:5173"
echo "   - バックエンドAPI: http://localhost:8000"
echo "   - APIドキュメント: http://localhost:8000/docs"
echo ""
echo "詳細は LOCAL_VERIFICATION_GUIDE.md を参照してください"
