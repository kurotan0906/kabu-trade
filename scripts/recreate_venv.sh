#!/bin/bash
# 仮想環境を再作成するスクリプト

set -e

echo "=================================================="
echo "仮想環境再作成スクリプト"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."
cd backend

# PATHにHomebrewのパスを追加
export PATH="/opt/homebrew/bin:$PATH"

# Python 3.11のパスを確認
PYTHON311="/opt/homebrew/bin/python3.11"
if [ ! -f "$PYTHON311" ]; then
    echo "✗ Python 3.11が見つかりません: $PYTHON311"
    echo "  HomebrewでPython 3.11をインストールしてください: brew install python@3.11"
    exit 1
fi

echo "Python 3.11のパス: $PYTHON311"
$PYTHON311 --version
echo ""

# 既存の仮想環境を削除
if [ -d "venv" ]; then
    echo "既存の仮想環境を削除中..."
    rm -rf venv
fi

# 仮想環境を作成（--without-pipオプションを使用）
echo "仮想環境を作成中..."
$PYTHON311 -m venv venv --without-pip

# 仮想環境を有効化
source venv/bin/activate

# pipをインストール
echo "pipをインストール中..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python

# pipをアップグレード
echo "pipをアップグレード中..."
pip install --upgrade pip

# 主要な依存関係をインストール
echo "主要な依存関係をインストール中..."
pip install fastapi uvicorn[standard] sqlalchemy alembic asyncpg psycopg2-binary redis httpx aiohttp python-dotenv pydantic-settings pydantic pandas numpy

echo ""
echo "=================================================="
echo "✓ 仮想環境の再作成が完了しました"
echo "=================================================="
echo ""
echo "Pythonバージョン: $(python --version)"
echo ""
echo "次のステップ:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
