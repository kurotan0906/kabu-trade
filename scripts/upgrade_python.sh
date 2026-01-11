#!/bin/bash
# Pythonアップグレードスクリプト

set -e

echo "=================================================="
echo "Python アップグレードスクリプト"
echo "=================================================="

# 現在のPythonバージョンを確認
CURRENT_PYTHON=$(python3 --version 2>&1 | awk '{print $2}')
echo "現在のPythonバージョン: $CURRENT_PYTHON"

# Python 3.11以上が必要
REQUIRED_VERSION="3.11"

# バージョン比較関数
version_ge() {
    if [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" = "$2" ]; then
        return 0
    else
        return 1
    fi
}

# 既にPython 3.11以上がインストールされているか確認
if version_ge "$CURRENT_PYTHON" "$REQUIRED_VERSION"; then
    echo "✓ Python $CURRENT_PYTHON は既に要件を満たしています"
    exit 0
fi

echo ""
echo "Python 3.11以上が必要です"
echo ""

# 利用可能なPythonバージョンを確認
echo "利用可能なPythonバージョンを確認中..."
PYTHON311=$(which python3.11 2>/dev/null || echo "")
PYTHON312=$(which python3.12 2>/dev/null || echo "")
PYTHON313=$(which python3.13 2>/dev/null || echo "")

if [ -n "$PYTHON311" ]; then
    echo "✓ Python 3.11が見つかりました: $PYTHON311"
    NEW_PYTHON="$PYTHON311"
elif [ -n "$PYTHON312" ]; then
    echo "✓ Python 3.12が見つかりました: $PYTHON312"
    NEW_PYTHON="$PYTHON312"
elif [ -n "$PYTHON313" ]; then
    echo "✓ Python 3.13が見つかりました: $PYTHON313"
    NEW_PYTHON="$PYTHON313"
else
    echo "✗ Python 3.11以上が見つかりません"
    echo ""
    echo "以下のいずれかの方法でPythonをインストールしてください："
    echo ""
    echo "1. Homebrewを使用（推奨）:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "   brew install python@3.11"
    echo ""
    echo "2. Python公式サイトからダウンロード:"
    echo "   https://www.python.org/downloads/"
    echo ""
    echo "詳細は PYTHON_UPGRADE.md を参照してください"
    exit 1
fi

# 新しいPythonバージョンを確認
NEW_VERSION=$($NEW_PYTHON --version 2>&1 | awk '{print $2}')
echo ""
echo "新しいPythonバージョン: $NEW_VERSION"
echo ""

# 仮想環境を再作成
echo "仮想環境を再作成中..."
cd "$(dirname "$0")/.."
cd backend

# 既存の仮想環境をバックアップ
if [ -d "venv" ]; then
    echo "既存の仮想環境をバックアップ中..."
    mv venv venv.backup.$(date +%Y%m%d_%H%M%S)
fi

# 新しいPythonで仮想環境を作成
echo "新しいPythonで仮想環境を作成中..."
$NEW_PYTHON -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipをアップグレード
echo "pipをアップグレード中..."
pip install --upgrade pip

# 依存関係をインストール
echo "依存関係をインストール中..."
pip install -r requirements.txt

echo ""
echo "=================================================="
echo "✓ Pythonアップグレードが完了しました"
echo "=================================================="
echo ""
echo "新しいPythonバージョン: $(python --version)"
echo ""
echo "次のステップ:"
echo "  1. 仮想環境を有効化: cd backend && source venv/bin/activate"
echo "  2. アプリケーションを起動: uvicorn app.main:app --reload"
echo ""
