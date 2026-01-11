#!/bin/bash
# バックエンドのみ起動スクリプト（データベースなしでも動作確認可能）

set -e

echo "=================================================="
echo "Kabu Trade バックエンド起動（データベースなしモード）"
echo "=================================================="

# プロジェクトルートに移動
cd "$(dirname "$0")/.."
cd backend

# 仮想環境の確認
if [ -z "$VIRTUAL_ENV" ]; then
    echo ""
    echo "仮想環境を有効化中..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "✗ 仮想環境が見つかりません"
        echo "  ./scripts/setup_local.sh を実行してください"
        exit 1
    fi
fi

# 環境変数ファイルの確認
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠ .envファイルが見つかりません"
    echo "  環境変数ファイルを作成しますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        cd ..
        ./scripts/create_env.sh
        cd backend
    else
        echo "  .envファイルを作成してください: ./scripts/create_env.sh"
        exit 1
    fi
fi

# バックエンド起動（データベース接続エラーを無視するモード）
echo ""
echo "バックエンドを起動中..."
echo "  URL: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "⚠ 注意: データベースが起動していない場合、一部の機能は動作しません"
echo "  モックデータでのAPI動作確認は可能です"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

# データベース接続エラーを無視して起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 || {
    echo ""
    echo "⚠ 起動に失敗しました"
    echo "  データベースを起動する場合: docker compose up -d postgres redis"
    exit 1
}
